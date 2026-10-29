"""Đọc file Excel/CSV thành list[dict] (dùng cho import sinh viên, danh sách đợt thực tập)."""
import csv
import io
from pathlib import Path

from openpyxl import load_workbook

from app.core.exceptions import BadRequestError


def read_rows(filename: str, content: bytes) -> list[dict[str, str]]:
    """Dòng đầu là header. Trả về list dict, giá trị đã strip, bỏ qua dòng trống hoàn toàn."""
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = [dict(r) for r in reader]
    elif ext == ".xlsx":
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheet = wb.active
        data = list(sheet.iter_rows(values_only=True))
        if not data:
            return []
        headers = [str(h).strip() if h is not None else "" for h in data[0]]
        rows = [dict(zip(headers, row, strict=False)) for row in data[1:]]
    else:
        raise BadRequestError("Chỉ hỗ trợ file .xlsx hoặc .csv")

    cleaned = []
    for row in rows:
        item = {k: ("" if v is None else str(v).strip()) for k, v in row.items() if k}
        if any(item.values()):
            cleaned.append(item)
    return cleaned
