"""Schema Pydantic: Nhà trường: quản lý dữ liệu sinh viên. Người phụ trách: TV2.

Cần có:
  - AdminStudentRead, AdminStudentDetail, StudentAcademicUpdate, ImportBatchRead, ImportRowError, AchievementCreate

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
