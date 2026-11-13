# Bật toàn bộ server: MariaDB → migration → Caddy → Cloudflare Tunnel → FastAPI → worker.
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\start-server.ps1
. (Join-Path $PSScriptRoot 'common.ps1')

if (Test-Path $PidFile) { throw 'Server có vẻ đang chạy (có processes.json). Chạy deploy\stop-server.ps1 trước.' }
foreach ($port in @($DbPort, $ApiPort, $WebPort)) {
  if (Test-Port $port) { throw "Cổng $port đang bị chiếm. Tắt ứng dụng đang dùng cổng này (vd start-local.ps1) rồi thử lại." }
}
if (-not (Test-Path (Join-Path $Dist 'index.html'))) { throw 'Chưa build frontend. Chạy: cd frontend; npm ci; npm run build' }

$cfg = Read-ServerEnv
Set-ProcessEnv $cfg
$pids = [ordered]@{}
function Save-Pids { $pids | ConvertTo-Json | Set-Content -Path $PidFile -Encoding UTF8 }

try {
  $pids.mariadb = (Start-MariaDB).Id; Save-Pids
  Invoke-Backend @('-m', 'alembic', '-c', 'alembic.ini', 'upgrade', 'head')

  $env:SC_FRONTEND_DIST = $Dist.Replace('\', '/')
  $pids.caddy = (Start-Hidden $Caddy @('run', '--config', "`"$(Join-Path $PSScriptRoot 'Caddyfile')`"", '--adapter', 'caddyfile') $Root 'caddy').Id; Save-Pids
  Wait-Port $WebPort 20 'Caddy'

  $tunnelLog = Join-Path $Logs 'cloudflared.log'
  Remove-Item $tunnelLog -ErrorAction SilentlyContinue
  if ($cfg.CF_TUNNEL_TOKEN) {
    if (-not $cfg.PUBLIC_URL) { throw 'Có CF_TUNNEL_TOKEN nhưng thiếu PUBLIC_URL trong server.env' }
    $publicUrl = $cfg.PUBLIC_URL.TrimEnd('/')
    # --url cho tunnel quản lý bằng CLI (không có ingress trên dashboard); tunnel tạo trên dashboard bỏ qua nó.
    $tunnelArgs = @('tunnel', '--no-autoupdate', '--logfile', "`"$tunnelLog`"", '--url', "http://127.0.0.1:$WebPort",
      'run', '--token', $cfg.CF_TUNNEL_TOKEN)
  } else {
    $publicUrl = $null
    $tunnelArgs = @('tunnel', '--no-autoupdate', '--logfile', "`"$tunnelLog`"", '--url', "http://127.0.0.1:$WebPort")
  }
  $pids.cloudflared = (Start-Hidden $Cloudflared $tunnelArgs $Root 'cloudflared').Id; Save-Pids
  if (-not $publicUrl) {
    for ($i = 0; $i -lt 60 -and -not $publicUrl; $i++) {
      Start-Sleep -Milliseconds 500
      $text = (Get-Content $tunnelLog, (Join-Path $Logs 'cloudflared-error.log') -Raw -ErrorAction SilentlyContinue) -join "`n"
      if ($text -match 'https://[a-z0-9-]+\.trycloudflare\.com') { $publicUrl = $Matches[0] }
    }
    if (-not $publicUrl) { throw 'Không lấy được URL trycloudflare. Xem logs\cloudflared*.log' }
  }

  # URL công khai dùng cho link trong email và chuyển hướng payOS
  $env:FRONTEND_URL = $publicUrl
  $env:CORS_ORIGINS = "[`"$publicUrl`"]"
  $env:PAYOS_RETURN_URL = "$publicUrl/payments/return"
  $env:PAYOS_CANCEL_URL = "$publicUrl/payments/cancel"
  $env:PAYOS_WEBHOOK_URL = "$publicUrl/api/v1/webhooks/payos/collection"

  $pids.api = (Start-Hidden $Py @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$ApiPort",
      '--proxy-headers', '--forwarded-allow-ips', '127.0.0.1', '--workers', '2') $Backend 'api').Id; Save-Pids
  $pids.worker = (Start-Hidden $Py @('-m', 'scripts.freelancer_worker', '--interval', '3') $Backend 'worker').Id; Save-Pids
  Wait-Port $ApiPort 40 'FastAPI'
  Set-Content -Path (Join-Path $Runtime 'public-url.txt') -Value $publicUrl -Encoding UTF8

  # URL tạm đổi mỗi lần chạy nên phải báo lại webhook cho payOS (payOS sẽ gọi thử URL này).
  if ($cfg.PAYOS_COLLECTION_ENABLED -eq 'true' -and $cfg.PAYOS_AUTO_REGISTER_WEBHOOK -eq 'true') {
    Start-Sleep -Seconds 5
    try { Invoke-Backend @('scripts/payos_webhook.py'); Write-Output "Đã đăng ký webhook payOS: $env:PAYOS_WEBHOOK_URL" }
    catch { Write-Warning "Đăng ký webhook payOS thất bại (server vẫn chạy): $_" }
  }
} catch {
  Write-Warning "Khởi động lỗi: $_ . Đang dọn các tiến trình đã bật..."
  & (Join-Path $PSScriptRoot 'stop-server.ps1') -NoBackup
  throw
}

Write-Output ''
Write-Output "Server đang chạy: $publicUrl"
Write-Output "API docs:         $publicUrl/docs"
Write-Output "Log:              $Logs"
Write-Output 'Tắt server:       powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\stop-server.ps1'
