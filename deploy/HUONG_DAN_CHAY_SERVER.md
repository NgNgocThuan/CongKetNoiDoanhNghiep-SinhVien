# Hướng dẫn chạy server Student Connect

Server công khai: **https://congketnoisinhvien.id.vn** (và `www.`).
Toàn bộ hệ thống chạy trên **một máy Windows**, đưa ra Internet qua Cloudflare Tunnel.
Chi tiết kỹ thuật: [README.md](README.md).

> **Quy tắc quan trọng:** mỗi lúc chỉ **một máy** được chạy server. Hai máy cùng chạy sẽ dùng
> chung tên miền nhưng hai database khác nhau, dữ liệu bị lệch. Muốn đổi máy: tắt máy cũ trước.

Mọi lệnh dưới đây chạy trong **PowerShell** tại thư mục gốc của repository.

---

## 1. Bật / tắt server (máy đã cài sẵn)

Bật:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\start-server.ps1
```

Khi thấy dòng `Server đang chạy: https://congketnoisinhvien.id.vn` là xong (khoảng 15–30 giây).
Có thể đóng cửa sổ PowerShell và ứng dụng khác, server vẫn chạy nền.

Tắt (tự backup database trước khi tắt):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\stop-server.ps1
```

Kiểm tra server còn sống: mở https://congketnoisinhvien.id.vn/health, phải thấy
`{"status":"ok","env":"production"}`.

Để server chạy liên tục:

- **Cắm sạc.** Khi chạy pin, Windows có thể cho máy ngủ sau vài phút làm web ngừng
  (chỉnh ở *Settings → System → Power & battery → Screen and sleep*).
- Không chạy `start-local.ps1` cùng lúc (trùng cổng 8000).
- Khởi động lại máy thì phải chạy lại lệnh bật.

Tài khoản demo và mật khẩu nằm trong `tmp\server-runtime\demo-accounts.txt` trên máy chủ
(không có trong Git). Hỏi người vận hành server.

---

## 2. Cập nhật code mới lên server

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\stop-server.ps1
git pull
cd frontend; npm ci; npm run build; cd ..
backend\.venv\Scripts\pip install -r backend\requirements.txt
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\start-server.ps1
```

Migration Alembic mới (nếu có) tự chạy khi bật server.

---

## 3. Cài server trên máy mới

### 3.1. Cài phần mềm (một lần)

```powershell
winget install Git.Git OpenJS.NodeJS.LTS Python.Python.3.13 MariaDB.Server CaddyServer.Caddy Cloudflare.cloudflared
```

Đóng và mở lại PowerShell sau khi cài. Lưu ý:

- Python phải là **CPython bản chính thức** (lệnh trên). Không dùng Python của MSYS2/MinGW
  (`C:\msys64\...`) vì không cài được `cryptography`, `pydantic-core`.
  Kiểm tra: `where.exe python` — dùng đường dẫn `...\Programs\Python\Python313\python.exe`.
- Node.js 22.12 trở lên.

### 3.2. Lấy code và cài thư viện

```powershell
git clone https://github.com/NgNgocThuan/CongKetNoiDoanhNghiep-SinhVien.git
cd CongKetNoiDoanhNghiep-SinhVien
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv backend\.venv
backend\.venv\Scripts\pip install -r backend\requirements.txt
cd frontend; npm ci; npm run build; cd ..
```

### 3.3. Cấu hình

**Trường hợp A — tiếp quản server đang chạy (giữ tên miền):**
chép file `tmp\server-runtime\server.env` từ máy cũ sang đúng vị trí đó trên máy mới
(bằng USB/đường riêng tư, **không gửi qua chat/email/Google Docs**). File này chứa token tunnel,
key payOS, mật khẩu Gmail và các khóa mã hóa. Không cần đăng nhập Cloudflare lại.

**Trường hợp B — dựng server mới hoàn toàn:** bỏ qua, bước 3.4 tự sinh `server.env` mới.
Server sẽ chạy bằng URL tạm `https://xxx.trycloudflare.com` (đổi mỗi lần bật) cho đến khi
gắn tên miền theo mục *Tên miền cố định* trong [README.md](README.md). Điền SMTP/Gemini/payOS
vào `tmp\server-runtime\server.env` rồi bật lại server.

### 3.4. Khởi tạo và bật

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\setup-server.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\start-server.ps1
```

`setup-server.ps1` chạy lại được nhiều lần, không ghi đè bí mật hay dữ liệu đã có. Nó tạo database,
chạy migration và 3 tài khoản demo (thêm `-NoDemo` nếu không muốn).

---

## 4. Thêm dữ liệu mẫu (tin tuyển dụng, doanh nghiệp, freelancer)

Chạy khi server **đang bật**:

```powershell
. .\deploy\common.ps1; Set-ProcessEnv (Read-ServerEnv); $env:PYTHONPATH = $Backend; $env:PYTHONIOENCODING = 'utf-8'
cd backend
.venv\Scripts\python -m scripts.seed_verified_actors
.venv\Scripts\python -m scripts.seed_demo_catalog
.venv\Scripts\python -m scripts.local_demo_seed
.venv\Scripts\python ..\deploy\rotate_demo_passwords.py ..\tmp\server-runtime\demo-accounts.txt
cd ..
```

**Luôn chạy dòng cuối** (`rotate_demo_passwords.py`): các script seed đặt mật khẩu `Password@123`
công khai trong repo, kể cả tài khoản admin. Script này đổi sang mật khẩu ngẫu nhiên và ghi vào
`demo-accounts.txt`. Không dùng `backend/database/seed_verified_actors.sql` (trỏ database
`student_connect_dev`, ID cố định).

---

## 5. Backup và khôi phục

- Mỗi lần tắt server sẽ có một file `tmp\server-runtime\backups\student-connect-<ngày-giờ>.scbak`
  (database + tài liệu tải lên + `server.env`, đã mã hóa). Giữ 14 bản gần nhất.
- Backup tay khi server đang bật: `powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\backup-server.ps1`
- Muốn có bản ngoài máy: đặt `BACKUP_COPY_DIR=` trong `server.env` là thư mục Google Drive/OneDrive.
- **Lưu riêng `BACKUP_ENCRYPTION_KEY`** (trình quản lý mật khẩu). Mất khóa là không mở được backup.

Khôi phục sang máy mới (làm sau bước 3.4 với `-NoDemo`, server đang bật).
*Các lệnh này chưa được chạy thử trên máy thật — kiểm tra kỹ trước khi dùng với dữ liệu quan trọng.*

```powershell
. .\deploy\common.ps1; $cfg = Read-ServerEnv; Write-ClientCnf $cfg.DB_ROOT_PASSWORD
$env:SC_BACKUP_KEY = $cfg.BACKUP_ENCRYPTION_KEY
& $Py deploy\backup_tool.py decrypt <đường-dẫn-file.scbak> tmp\restore
$sql = (Get-ChildItem tmp\restore\db-*.sql).FullName.Replace('\','/')
Invoke-Maria $MariaCli @('--default-character-set=utf8mb4', $DbName, "--execute=source $sql")
Copy-Item tmp\restore\uploads\* $Uploads -Recurse -Force
Remove-Item Env:SC_BACKUP_KEY; Remove-Item tmp\restore -Recurse -Force
```

Sau đó tắt rồi bật lại server.

---

## 6. Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `Cổng 8000/8080/3306 đang bị chiếm` | Tắt `start-local.ps1`, MySQL/XAMPP/Laragon hoặc server cũ (`stop-server.ps1`) |
| `Server có vẻ đang chạy (có processes.json)` | Chạy `stop-server.ps1` trước; nếu máy vừa tắt đột ngột thì xóa `tmp\server-runtime\processes.json` |
| Máy mình không vào được tên miền nhưng máy khác vào được | Windows nhớ DNS cũ: chạy `ipconfig /flushdns` |
| Chữ tiếng Việt trong script bị lỗi font khi chạy | File `.ps1` phải lưu dạng UTF-8 **có BOM** (Windows PowerShell 5.1) |
| `pip install` lỗi `cryptography`/`pydantic-core` | Đang dùng Python MSYS2 — tạo lại `backend\.venv` bằng CPython (mục 3.1) |
| `/health` trên URL `trycloudflare` trả trang trống | Bình thường (Cloudflare chặn đường dẫn này trên URL tạm); dùng tên miền riêng |
| Lỗi khác | Xem log trong `tmp\server-runtime\logs\` (`api-error.log`, `worker-error.log`, `cloudflared.log`, `mariadb-error.log`) |

---

## 7. Giới hạn hiện tại

- Server là máy cá nhân: tắt máy/ngủ/mất mạng là web ngừng, chưa tự bật lại sau khi khởi động máy.
- payOS: thu tiền bật; **chi tiền tắt** (`PAYOS_PAYOUT_ENABLED=false`) vì IP nhà mạng thay đổi.
- Script chỉ dành cho Windows.
