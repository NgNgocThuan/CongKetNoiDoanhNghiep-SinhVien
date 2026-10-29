"""Schema Pydantic: Tin tuyển dụng. Người phụ trách: TV4.

Cần có:
  - JobCreate, JobUpdate, JobRead, JobListItem, JobFilter, JobSkillIn, JobStats

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
