"""Tính điểm phù hợp (Matching Score). Người phụ trách: TV5.

Nguyên tắc (theo đặc tả): điểm chỉ là GỢI Ý, không phải kết luận tuyển dụng tự động.
BACKEND kiểm soát cách tính điểm; LLM chỉ trích xuất dữ liệu và giải thích, không quyết định điểm.
Module này thuần tính toán (không gọi DB/API) để dễ unit test.
"""
from dataclasses import dataclass, field

ALGO_VERSION = "1.0"

# Trọng số mặc định, TV5 chỉnh và ghi lại lý do trong docs
WEIGHTS = {"skill": 0.5, "experience": 0.2, "semantic": 0.3}


@dataclass
class MatchBreakdown:
    passed_rules: bool
    failed_rules: list[str] = field(default_factory=list)
    score: float = 0.0  # 0-100
    skill_score: float = 0.0
    experience_score: float = 0.0
    semantic_score: float = 0.0
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    explanation: str = ""


def check_hard_rules(student, job, *, in_term: bool) -> list[str]:
    """Trả về danh sách điều kiện bắt buộc KHÔNG đạt (rỗng = đạt hết).

    TODO(TV5): ngành học (job.majors), GPA tối thiểu (job.min_gpa), luồng tuyển dụng
    (job.term_id -> cần in_term), tin phải APPROVED và còn hạn.
    """
    raise NotImplementedError


def compute_match(student, job, cv_parsed: dict | None, job_parsed: dict | None, *, in_term: bool) -> MatchBreakdown:
    """TODO(TV5): so khớp kỹ năng (bắt buộc nặng hơn ưu tiên), kinh nghiệm, ngữ nghĩa/từ khóa;
    nếu không đạt điều kiện bắt buộc thì passed_rules=False và score=0."""
    raise NotImplementedError
