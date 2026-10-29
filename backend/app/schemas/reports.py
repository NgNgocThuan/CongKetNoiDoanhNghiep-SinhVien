"""Schema Pydantic: Báo cáo vi phạm. Người phụ trách: TV1.

Cần có:
  - ReportCreate, ReportRead, ReportHandle

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
