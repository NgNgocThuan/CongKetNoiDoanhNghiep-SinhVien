"""Schema Pydantic: Hồ sơ sinh viên (phía sinh viên). Người phụ trách: TV3.

Cần có:
  - StudentOfficialRead, StudentSelfRead, StudentFullProfile, ProfileUpdate, SkillItem, ExperienceCreate/Update/Read, ProjectCreate/Update/Read, CertificateCreate/Update/Read

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
