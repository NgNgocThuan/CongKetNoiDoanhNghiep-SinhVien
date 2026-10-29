"""Schema Pydantic: AI Job Matching. Người phụ trách: TV5.

Cần có:
  - MatchResult, JobRecommendation, CandidateRecommendation (đã ẩn trường theo quyền riêng tư)

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
