"""Nghiệp vụ: Xuất báo cáo Excel/PDF. Người phụ trách: TV5.

Hàm cần viết:
  - Mỗi báo cáo một hàm trả bytes/stream (openpyxl cho Excel; thêm thư viện PDF vào requirements)
  - Phân quyền dữ liệu: KHÔNG xuất thông tin cá nhân không cần thiết (SĐT, ngày sinh...) trừ khi báo cáo thật sự cần

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
