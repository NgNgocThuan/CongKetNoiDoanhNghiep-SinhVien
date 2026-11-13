# Đường dẫn và hàm dùng chung cho các script server tự host trên Windows.
$ErrorActionPreference = 'Stop'

$Root      = Split-Path $PSScriptRoot -Parent
$Backend   = Join-Path $Root 'backend'
$Frontend  = Join-Path $Root 'frontend'
$Dist      = Join-Path $Frontend 'dist'
$Runtime   = Join-Path $Root 'tmp\server-runtime'
$DataDir   = Join-Path $Runtime 'mariadb-data'
$Uploads   = Join-Path $Runtime 'uploads'
$Logs      = Join-Path $Runtime 'logs'
$Backups   = Join-Path $Runtime 'backups'
$EnvFile   = Join-Path $Runtime 'server.env'
$PidFile   = Join-Path $Runtime 'processes.json'
$Py        = Join-Path $Backend '.venv\Scripts\python.exe'
$DbName    = 'student_connect'
$DbPort    = 3306
$ApiPort   = 8000
$WebPort   = 8080

function Find-Exe([string]$Name, [string[]]$Fallbacks) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  foreach ($f in $Fallbacks) { if (Test-Path $f) { return $f } }
  throw "Không tìm thấy $Name. Cài bằng: winget install $Name"
}

$mariaDir = Get-ChildItem 'C:\Program Files' -Directory -Filter 'MariaDB*' -ErrorAction SilentlyContinue |
  Sort-Object Name -Descending | Select-Object -First 1
if (-not $mariaDir) { throw 'Chưa cài MariaDB. Chạy: winget install MariaDB.Server' }
$MariaBin   = Join-Path $mariaDir.FullName 'bin'
$Mariadbd   = Join-Path $MariaBin 'mariadbd.exe'
$MariaCli   = Join-Path $MariaBin 'mariadb.exe'
$MariaAdmin = Join-Path $MariaBin 'mariadb-admin.exe'
$MariaDump  = Join-Path $MariaBin 'mariadb-dump.exe'
$MariaInit  = Join-Path $MariaBin 'mariadb-install-db.exe'
$Caddy       = Find-Exe 'caddy' @("$env:LOCALAPPDATA\Microsoft\WinGet\Links\caddy.exe")
$Cloudflared = Find-Exe 'cloudflared' @('C:\Program Files (x86)\cloudflared\cloudflared.exe', 'C:\Program Files\cloudflared\cloudflared.exe')

function Read-ServerEnv {
  if (-not (Test-Path $EnvFile)) { throw "Chưa có $EnvFile. Chạy deploy\setup-server.ps1 trước." }
  $h = [ordered]@{}
  foreach ($line in Get-Content $EnvFile -Encoding UTF8) {
    if ($line -match '^\s*([A-Z][A-Z0-9_]*)\s*=(.*)$') { $h[$Matches[1]] = $Matches[2].Trim() }
  }
  return $h
}

function Set-ProcessEnv($h) {
  foreach ($k in $h.Keys) { [Environment]::SetEnvironmentVariable($k, [string]$h[$k], 'Process') }
}

function Test-Port([int]$Port) {
  [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Port([int]$Port, [int]$Seconds, [string]$What) {
  for ($i = 0; $i -lt $Seconds * 2; $i++) {
    if (Test-Port $Port) { return }
    Start-Sleep -Milliseconds 500
  }
  throw "$What không mở cổng $Port sau $Seconds giây. Xem log trong $Logs"
}

function Start-Hidden([string]$Exe, [string[]]$Arguments, [string]$Cwd, [string]$LogName) {
  Start-Process -FilePath $Exe -ArgumentList $Arguments -WorkingDirectory $Cwd -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $Logs "$LogName.log") -RedirectStandardError (Join-Path $Logs "$LogName-error.log")
}

function Start-MariaDB {
  if (Test-Port $DbPort) { throw "Cổng $DbPort đang bị chiếm (có MariaDB/MySQL khác đang chạy?)." }
  $p = Start-Hidden $Mariadbd @("--datadir=`"$DataDir`"", "--port=$DbPort", '--bind-address=127.0.0.1',
    '--character-set-server=utf8mb4', '--collation-server=utf8mb4_unicode_ci') $Runtime 'mariadb'
  Wait-Port $DbPort 60 'MariaDB'
  return $p
}

# File client chứa mật khẩu root (nằm trong tmp\, không commit) để không lộ mật khẩu trên dòng lệnh.
$ClientCnf = Join-Path $Runtime 'client.cnf'
function Write-ClientCnf([string]$RootPassword) {
  "[client]`nuser=root`npassword=$RootPassword`nhost=127.0.0.1`nport=$DbPort`n" |
    Set-Content -Path $ClientCnf -Encoding ASCII
}

function Invoke-Maria([string]$Exe, [string[]]$Arguments) {
  $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { & $Exe "--defaults-extra-file=$ClientCnf" @Arguments 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'ssl-verify-server-cert' } }
  finally { $ErrorActionPreference = $old }
}

function Stop-MariaDB {
  if (-not (Test-Port $DbPort)) { return }
  Invoke-Maria $MariaAdmin @('shutdown') | Out-Null
  for ($i = 0; $i -lt 60 -and (Test-Port $DbPort); $i++) { Start-Sleep -Milliseconds 500 }
}

function Invoke-Backend([string[]]$Arguments) {
  Push-Location $Backend
  try {
    & $Py @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Lệnh backend thất bại: $($Arguments -join ' ')" }
  } finally { Pop-Location }
}
