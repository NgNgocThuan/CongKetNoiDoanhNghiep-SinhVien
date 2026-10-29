"""Schema Pydantic: Quản lý CV. Người phụ trách: TV3.

Cần có:
  - CVRead, CVOnlineCreate, CVUpdate

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
