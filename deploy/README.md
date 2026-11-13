# Server tự host trên Windows (bật khi cần)

Hướng dẫn từng bước cho người vận hành (bật/tắt, cập nhật, máy mới, seed, backup, lỗi thường gặp):
[HUONG_DAN_CHAY_SERVER.md](HUONG_DAN_CHAY_SERVER.md).

```
Internet ─▶ Cloudflare Tunnel (HTTPS) ─▶ Caddy 127.0.0.1:8080 ─┬─▶ frontend/dist (React)
                                                               └─▶ FastAPI 127.0.0.1:8000 ─▶ MariaDB 127.0.0.1:3306
                                                                   Worker (scripts.freelancer_worker) ─┘
```

Không mở cổng modem, không cần IP tĩnh. Mọi dịch vụ chỉ nghe `127.0.0.1`.

## Cài một lần

1. `winget install MariaDB.Server CaddyServer.Caddy Cloudflare.cloudflared`
2. Python 3.11+ **bản CPython** (không dùng python của MSYS2):
   `python -m venv backend\.venv` rồi `backend\.venv\Scripts\pip install -r backend\requirements.txt`
3. `cd frontend; npm ci; npm run build`
4. `powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\setup-server.ps1`
   - Sinh bí mật vào `tmp\server-runtime\server.env` (không commit).
   - Tạo database riêng trong `tmp\server-runtime\mariadb-data`, chạy migration.
   - Tạo tài khoản demo với mật khẩu ngẫu nhiên: `tmp\server-runtime\demo-accounts.txt`.

## Hằng ngày

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\start-server.ps1   # in ra URL công khai
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\stop-server.ps1    # backup rồi tắt
```

Cập nhật code: tắt server → `git pull` → `cd frontend; npm ci; npm run build` → bật lại (migration tự chạy).

Không chạy `start-local.ps1` cùng lúc vì trùng cổng 8000.

## Tên miền cố định (đang dùng: https://congketnoisinhvien.id.vn)

Đã cấu hình: tên miền đăng ký ở Tenten, nameserver `corey.ns.cloudflare.com` / `heidi.ns.cloudflare.com`,
tunnel `congketnoi-server` (tạo bằng CLI), CNAME `@` và `www` trỏ vào tunnel.
Webhook payOS đã đăng ký: `https://congketnoisinhvien.id.vn/api/v1/webhooks/payos/collection` (không cần đăng ký lại mỗi lần bật).

Làm lại trên máy khác / tên miền khác:

1. Thêm tên miền vào Cloudflare (gói Free), đổi nameserver ở nhà đăng ký sang 2 nameserver Cloudflare cấp.
2. `cloudflared tunnel login` → chọn tên miền → Authorize.
3. `cloudflared tunnel create <tên>`; `cloudflared tunnel route dns <tên> <tên-miền>` (và `www.<tên-miền>`).
4. `cloudflared tunnel token <tên>` → dán vào `CF_TUNNEL_TOKEN`; đặt `PUBLIC_URL=https://<tên-miền>` trong `server.env`.
5. Tắt rồi bật lại server. Đăng ký webhook payOS một lần (hoặc đặt `PAYOS_AUTO_REGISTER_WEBHOOK=true` cho một lần bật).

`%USERPROFILE%\.cloudflared\cert.pem` và file `*.json` trong đó là bí mật của tài khoản Cloudflare, không chia sẻ.

## Bí mật, email, payOS

Sửa `tmp\server-runtime\server.env` rồi khởi động lại:
- Gmail: `SMTP_HOST=smtp.gmail.com`, `SMTP_USER`, `SMTP_PASSWORD` (App Password), `SMTP_FROM`.
- payOS: điền key, bật `FREELANCER_FINANCE_ENABLED` và `PAYOS_COLLECTION_ENABLED` **chỉ khi đã có tên miền cố định**;
  webhook là `PUBLIC_URL/api/v1/webhooks/payos/collection`. Giữ `PAYOS_PAYOUT_ENABLED=false` trên mạng gia đình.

## Backup

- `stop-server.ps1` tự backup; chạy tay: `deploy\backup-server.ps1` (khi server đang bật).
- File `tmp\server-runtime\backups\*.scbak` = dump MariaDB + uploads + server.env, mã hóa bằng `BACKUP_ENCRYPTION_KEY`. Giữ 14 bản.
- Đặt `BACKUP_COPY_DIR` là thư mục Google Drive / OneDrive để có bản ngoài máy.
- **Lưu `BACKUP_ENCRYPTION_KEY` ở nơi khác** (trình quản lý mật khẩu). Mất khóa = không mở được backup.
- Giải mã: `$env:SC_BACKUP_KEY='<key>'; backend\.venv\Scripts\python deploy\backup_tool.py decrypt <file.scbak> <thư-mục>`

## Giới hạn

- Tắt máy/sleep/mất mạng thì web ngừng; webhook payOS lúc đó thất bại.
- URL `*.trycloudflare.com` đổi mỗi lần bật; đường dẫn `/health` bị Cloudflare chặn trên URL tạm (bình thường trên tên miền riêng).
