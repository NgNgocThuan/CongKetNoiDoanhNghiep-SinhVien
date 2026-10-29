"""Schema Pydantic: Hồ sơ doanh nghiệp. Người phụ trách: TV4.

Cần có:
  - CompanyRead, CompanyUpdate, CompanyPublicRead, CompanyDocumentRead

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
