# Chuẩn bị server lần đầu (chạy lại được, không ghi đè bí mật hay dữ liệu đã có).
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\setup-server.ps1
#   Thêm -NoDemo nếu không muốn tạo tài khoản demo.
param([switch]$NoDemo)
. (Join-Path $PSScriptRoot 'common.ps1')

foreach ($d in @($Runtime, $DataDir, $Uploads, $Logs, $Backups)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
if (-not (Test-Path $Py)) { throw "Chưa có backend\.venv. Tạo bằng Python 3.11+ (không dùng bản MSYS2): python -m venv backend\.venv; backend\.venv\Scripts\pip install -r backend\requirements.txt" }

# 1. Sinh bí mật một lần duy nhất
if (-not (Test-Path $EnvFile)) {
  $gen = & $Py -c @'
import secrets
from cryptography.fernet import Fernet
t = lambda n=36: secrets.token_urlsafe(n)
print(t(24)); print(t(24)); print(t(48)); print(t(48)); print(Fernet.generate_key().decode()); print(t(48)); print(Fernet.generate_key().decode())
'@
  $rootPw, $appPw, $secret, $otp, $bankKey, $bankFp, $backupKey = $gen
  $uploadsFwd = $Uploads.Replace('\', '/')
  @"
# Bí mật của server tự host. KHÔNG commit, KHÔNG gửi qua chat.
# Lưu riêng một bản BACKUP_ENCRYPTION_KEY và FREELANCER_BANK_ENCRYPTION_KEY ở nơi an toàn khác.
ENV=production
DEBUG=false
DB_ROOT_PASSWORD=$rootPw
DB_APP_PASSWORD=$appPw
DATABASE_URL=mysql+pymysql://app:$appPw@127.0.0.1:$DbPort/$($DbName)?charset=utf8mb4
SECRET_KEY=$secret
FREELANCER_OTP_SECRET=$otp
FREELANCER_BANK_ENCRYPTION_KEY=$bankKey
FREELANCER_BANK_KEY_VERSION=v1
FREELANCER_BANK_FINGERPRINT_KEY=$bankFp
BACKUP_ENCRYPTION_KEY=$backupKey
UPLOAD_DIR=$uploadsFwd

# Tên miền cố định: dán token tunnel Cloudflare và URL công khai (vd https://studentconnect.me).
# Để trống thì start-server.ps1 dùng URL tạm *.trycloudflare.com (đổi mỗi lần chạy).
CF_TUNNEL_TOKEN=
PUBLIC_URL=

# Thư mục được đồng bộ ra ngoài máy (vd thư mục Google Drive for desktop). Trống = chỉ lưu local.
BACKUP_COPY_DIR=

# Email (Gmail: smtp.gmail.com, 587, App Password)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_SSL=false

AI_PROVIDER=gemini
AI_API_KEY=
AI_MODEL=

# payOS: chỉ bật khi đã có key và tên miền cố định. Không bật chi tiền khi IP nhà mạng thay đổi.
FREELANCER_FINANCE_ENABLED=false
PAYOS_COLLECTION_ENABLED=false
PAYOS_PAYOUT_ENABLED=false
PAYOS_COLLECTION_CLIENT_ID=
PAYOS_COLLECTION_API_KEY=
PAYOS_COLLECTION_CHECKSUM_KEY=
PAYOS_COLLECTION_BANK_BIN=
PAYOS_COLLECTION_ACCOUNT_NUMBER=
PAYOS_PAYOUT_CLIENT_ID=
PAYOS_PAYOUT_API_KEY=
PAYOS_PAYOUT_CHECKSUM_KEY=
"@ | Set-Content -Path $EnvFile -Encoding UTF8
  Write-Output "Đã tạo $EnvFile"
}
$cfg = Read-ServerEnv
Set-ProcessEnv $cfg
Write-ClientCnf $cfg.DB_ROOT_PASSWORD

# 2. Khởi tạo thư mục dữ liệu MariaDB riêng
if (-not (Get-ChildItem $DataDir -Force | Select-Object -First 1)) {
  & $MariaInit "--datadir=$DataDir" "--password=$($cfg.DB_ROOT_PASSWORD)" | Out-File (Join-Path $Logs 'mariadb-init.log') -Encoding UTF8
  if ($LASTEXITCODE -ne 0) { throw 'Khởi tạo MariaDB thất bại, xem logs\mariadb-init.log' }
  Write-Output 'Đã khởi tạo dữ liệu MariaDB'
}

$db = Start-MariaDB
try {
  $sql = @"
CREATE DATABASE IF NOT EXISTS $DbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'app'@'localhost' IDENTIFIED BY '$($cfg.DB_APP_PASSWORD)';
CREATE USER IF NOT EXISTS 'app'@'127.0.0.1' IDENTIFIED BY '$($cfg.DB_APP_PASSWORD)';
GRANT ALL PRIVILEGES ON $DbName.* TO 'app'@'localhost';
GRANT ALL PRIVILEGES ON $DbName.* TO 'app'@'127.0.0.1';
FLUSH PRIVILEGES;
"@
  Invoke-Maria $MariaCli @("--execute=$sql")
  if ($LASTEXITCODE -ne 0) { throw 'Tạo database/user thất bại' }

  # 3. Migration
  Invoke-Backend @('-m', 'alembic', '-c', 'alembic.ini', 'upgrade', 'head')
  Write-Output 'Migration xong'

  # 4. Dữ liệu danh mục + tài khoản demo với mật khẩu ngẫu nhiên (không dùng Password@123 công khai)
  if (-not $NoDemo) {
    $accounts = Join-Path $Runtime 'demo-accounts.txt'
    Invoke-Backend @('-c', @"
import secrets
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User
from scripts.seed import seed
out = r'$accounts'
with SessionLocal() as db:
    seed(db)
    db.commit()
    import os
    if not os.path.exists(out):
        lines = []
        for email in ('admin@school.edu.vn', 'sv001@school.edu.vn', 'hr@acme.vn'):
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                continue
            pw = 'Sc-' + secrets.token_urlsafe(9)
            user.password_hash = hash_password(pw)
            lines.append(f'{email}  {pw}')
        db.commit()
        open(out, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
"@)
    Write-Output "Tài khoản demo: xem $accounts"
  }
} finally {
  try { Stop-MariaDB } finally { if ($db -and -not $db.HasExited) { $db.Kill() } }
}

# 5. Build frontend nếu chưa có
if (-not (Test-Path (Join-Path $Dist 'index.html'))) {
  Push-Location $Frontend
  try { npm ci --no-audit --no-fund; npm run build; if ($LASTEXITCODE -ne 0) { throw 'Build frontend thất bại' } }
  finally { Pop-Location }
}
Write-Output 'Setup xong. Bật server: powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\start-server.ps1'
