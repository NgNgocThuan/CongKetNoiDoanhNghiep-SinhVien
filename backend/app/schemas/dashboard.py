"""Schema Pydantic: Dashboard thống kê nhà trường. Người phụ trách: TV5.

Cần có:
  - OverviewStats, BreakdownRow, SkillStat, SkillGapRow, MatchRateRow, TrendPoint, FlowComparison

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
