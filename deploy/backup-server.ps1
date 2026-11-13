# Backup mã hóa: dump MariaDB + thư mục uploads + server.env → tmp\server-runtime\backups\*.scbak
# Cần MariaDB đang chạy. Giữ 14 bản gần nhất; sao chép sang BACKUP_COPY_DIR nếu có.
. (Join-Path $PSScriptRoot 'common.ps1')

$cfg = Read-ServerEnv
if (-not (Test-Port $DbPort)) { throw 'MariaDB chưa chạy, không backup được.' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dump = Join-Path $Backups "db-$stamp.sql"
Write-ClientCnf $cfg.DB_ROOT_PASSWORD
Invoke-Maria $MariaDump @('--single-transaction', '--routines', '--triggers',
  '--default-character-set=utf8mb4', "--result-file=$dump", $DbName)
if ($LASTEXITCODE -ne 0) { throw 'mariadb-dump thất bại' }

$out = Join-Path $Backups "student-connect-$stamp.scbak"
$env:SC_BACKUP_KEY = $cfg.BACKUP_ENCRYPTION_KEY
& $Py (Join-Path $PSScriptRoot 'backup_tool.py') encrypt $out $dump $Uploads $EnvFile
$code = $LASTEXITCODE
Remove-Item Env:SC_BACKUP_KEY
Remove-Item $dump
if ($code -ne 0) { throw 'Mã hóa backup thất bại' }

Get-ChildItem $Backups -Filter '*.scbak' | Sort-Object Name -Descending | Select-Object -Skip 14 | Remove-Item
if ($cfg.BACKUP_COPY_DIR) {
  New-Item -ItemType Directory -Force -Path $cfg.BACKUP_COPY_DIR | Out-Null
  Copy-Item $out $cfg.BACKUP_COPY_DIR
}
Write-Output "Backup: $out"
