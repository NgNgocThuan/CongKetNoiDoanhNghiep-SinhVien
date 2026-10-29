"""AI Job Matching: kết quả so khớp (cache) và nhật ký gọi API NLP."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AIPurpose, AIRequestStatus
from app.models.base import ID, Base, CreatedAtMixin, UInt, db_enum, fk, pk


class MatchingResult(Base):
    """Mỗi cặp (sinh viên, tin) một dòng. input_hash đổi => kết quả cũ hết hiệu lực, tính lại.

    Điểm do BACKEND tính từ passed_rules + skill/experience; LLM chỉ trích xuất và giải thích.
    """

    __tablename__ = "matching_results"

    id: Mapped[int] = pk()
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    job_id: Mapped[int] = fk("jobs.id", ondelete="CASCADE")
    cv_id: Mapped[Optional[int]] = fk("cvs.id", ondelete="SET NULL", nullable=True)
    passed_rules: Mapped[bool] = mapped_column(nullable=False)  # đạt điều kiện bắt buộc
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # 0-100
    skill_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    experience_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    semantic_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    matched_skills: Mapped[Optional[list]] = mapped_column(JSON)
    missing_skills: Mapped[Optional[list]] = mapped_column(JSON)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(100))
    algo_version: Mapped[Optional[str]] = mapped_column(String(20))
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "job_id", name="uq_matching_student_job"),
        Index("idx_matching_job_score", "job_id", "score"),
        Index("idx_matching_student_score", "student_id", "score"),
        CheckConstraint("score >= 0 AND score <= 100", name="score_range"),
    )


class AIRequestLog(CreatedAtMixin, Base):
    """Theo dõi gọi API NLP: chi phí, lỗi, độ trễ."""

    __tablename__ = "ai_request_logs"

    id: Mapped[int] = pk()
    purpose: Mapped[AIPurpose] = mapped_column(db_enum(AIPurpose), nullable=False)
    ref_type: Mapped[Optional[str]] = mapped_column(String(30))
    ref_id: Mapped[Optional[int]] = mapped_column(ID)
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    model_name: Mapped[Optional[str]] = mapped_column(String(100))
    input_tokens: Mapped[Optional[int]] = mapped_column(UInt)
    output_tokens: Mapped[Optional[int]] = mapped_column(UInt)
    status: Mapped[AIRequestStatus] = mapped_column(db_enum(AIRequestStatus), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    latency_ms: Mapped[Optional[int]] = mapped_column(UInt)

    __table_args__ = (
        Index("idx_ai_logs_ref", "ref_type", "ref_id"),
        Index("idx_ai_logs_time", "created_at"),
    )
