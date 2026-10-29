"""Schema Pydantic: Ứng tuyển & theo dõi đơn (phía sinh viên). Người phụ trách: TV3.

Cần có:
  - ApplicationCreate, ApplicationRead, ApplicationDetail, StatusLogRead

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
