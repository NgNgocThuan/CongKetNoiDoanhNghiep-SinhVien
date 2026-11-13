"""Resolve free-text tags immediately while preserving catalog IDs."""
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ConflictError
from app.models.catalog import Skill, SkillAlias


def resolve_in_tx(db, name):
    name = " ".join(unicodedata.normalize("NFKC", name).split()).casefold()
    if not name or len(name) > 100 or any(c in '<>"`\\' or unicodedata.category(c).startswith('C') for c in name):
        raise BadRequestError("Kỹ năng cần từ 1 đến 100 ký tự, không chứa mã đánh dấu hoặc ký tự điều khiển")
    row = db.scalar(select(Skill).where(func.lower(Skill.name) == name))
    if row is None:
        row = db.scalar(select(Skill).join(SkillAlias).where(func.lower(SkillAlias.alias) == name))
    if row is None:
        try:
            with db.begin_nested():
                row = Skill(name=name, category="OTHER", is_active=True)
                db.add(row)
                db.flush()
        except IntegrityError:
            row = db.scalar(select(Skill).where(func.lower(Skill.name) == name))
            if row is None:
                raise ConflictError("Kỹ năng vừa được cập nhật; vui lòng thử lại") from None
    if not row.is_active:
        raise BadRequestError("Kỹ năng này đã ngừng sử dụng")
    return row
