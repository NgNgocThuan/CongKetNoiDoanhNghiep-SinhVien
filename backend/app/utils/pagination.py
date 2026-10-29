"""Phân trang dùng chung cho mọi API danh sách."""
import math

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas.common import PageParams


def paginate(db: Session, stmt: Select, params: PageParams) -> dict:
    """Chạy `stmt` (đã có where/order_by) và trả dict khớp schema Page[T]."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.offset(params.offset).limit(params.size)).all()
    pages = math.ceil(total / params.size) if total else 0
    return {"items": items, "total": total, "page": params.page, "size": params.size, "pages": pages}
