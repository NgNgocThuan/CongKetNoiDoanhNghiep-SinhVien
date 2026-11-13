# Tắt server; mặc định backup database + tài liệu trước khi tắt MariaDB.
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\stop-server.ps1 [-NoBackup]
param([switch]$NoBackup)
. (Join-Path $PSScriptRoot 'common.ps1')

$cfg = Read-ServerEnv
$pids = if (Test-Path $PidFile) { Get-Content $PidFile -Raw | ConvertFrom-Json } else { $null }

function Stop-Tree($procId) {
  if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) { taskkill /PID $procId /T /F *> $null }
}

# Ngừng nhận request trước, rồi worker/API
if ($pids) { foreach ($name in @('cloudflared', 'caddy', 'worker', 'api')) { Stop-Tree $pids.$name } }

if ((Test-Port $DbPort) -and -not $NoBackup) {
  try { & (Join-Path $PSScriptRoot 'backup-server.ps1') } catch { Write-Warning "Backup lỗi: $_" }
}
Write-ClientCnf $cfg.DB_ROOT_PASSWORD
Stop-MariaDB
if ($pids) { Stop-Tree $pids.mariadb }

Remove-Item $PidFile -ErrorAction SilentlyContinue
Write-Output 'Server đã tắt.'
