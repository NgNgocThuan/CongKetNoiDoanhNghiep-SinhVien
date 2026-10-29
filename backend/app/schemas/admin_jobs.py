"""Schema Pydantic: Nhà trường: kiểm duyệt tin tuyển dụng. Người phụ trách: TV1.

Cần có:
  - Dùng lại JobRead (schemas/jobs.py của TV4) + RejectRequest

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
