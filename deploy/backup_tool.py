"""Đóng gói + mã hóa (Fernet) bản backup, và giải mã khi khôi phục.

Khóa lấy từ biến môi trường SC_BACKUP_KEY (= BACKUP_ENCRYPTION_KEY trong server.env).
  python backup_tool.py encrypt <out.scbak> <file-or-dir>...
  python backup_tool.py decrypt <in.scbak> <out-dir>
"""

import io
import os
import sys
import zipfile
from pathlib import Path

from cryptography.fernet import Fernet


def fernet() -> Fernet:
    key = os.environ.get("SC_BACKUP_KEY", "").strip()
    if not key:
        sys.exit("Thiếu SC_BACKUP_KEY")
    return Fernet(key.encode())


def encrypt(out: Path, sources: list[Path]) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for src in sources:
            if src.is_dir():
                for f in src.rglob("*"):
                    if f.is_file():
                        zf.write(f, Path(src.name) / f.relative_to(src))
            elif src.is_file():
                zf.write(src, src.name)
    out.write_bytes(fernet().encrypt(buf.getvalue()))


def decrypt(src: Path, out_dir: Path) -> None:
    data = fernet().decrypt(src.read_bytes())
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(out_dir)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "encrypt":
        encrypt(Path(sys.argv[2]), [Path(p) for p in sys.argv[3:]])
    elif len(sys.argv) == 4 and sys.argv[1] == "decrypt":
        decrypt(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        sys.exit(__doc__)
