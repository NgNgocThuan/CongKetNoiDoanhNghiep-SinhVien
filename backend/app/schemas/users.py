"""Schema Pydantic: Quản lý tài khoản (admin). Người phụ trách: TV1.

Cần có:
  - UserRead, UserFilter, LockUserRequest, AdminCreate

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
