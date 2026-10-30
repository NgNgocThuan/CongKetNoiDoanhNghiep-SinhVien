"""Thông báo trong ứng dụng. Người phụ trách: TV1."""
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Notification, User
from app.schemas.common import PageParams
from app.utils.pagination import paginate


def create_notification(
    db: Session,
    *,
    user_id: int,
    type: str,
    title: str,
    content: Optional[str] = None,
    ref_type: Optional[str] = None,
    ref_id: Optional[int] = None,
    commit: bool = True,
) -> Notification:
    """Tạo thông báo cho một user. Truyền commit=False nếu đang nằm trong transaction lớn hơn."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        ref_type=ref_type,
        ref_id=ref_id,
    )
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    else:
        db.flush()
    return notification


def list_notifications(
    db: Session,
    user: User,
    params: PageParams,
    *,
    is_read: Optional[bool] = None,
) -> dict:
    """Lấy danh sách thông báo của người dùng kèm phân trang."""
    stmt = select(Notification).where(Notification.user_id == user.id)

    if is_read is not None:
        stmt = stmt.where(Notification.is_read.is_(is_read))

    stmt = stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
    return paginate(db, stmt, params)


def unread_count(db: Session, user: User) -> int:
    """Đếm số thông báo chưa đọc của người dùng."""
    stmt = (
        select(func.count(Notification.id))
        .where(Notification.user_id == user.id)
        .where(Notification.is_read.is_(False))
    )
    return db.scalar(stmt) or 0


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    """Đánh dấu một thông báo đã đọc (sai quyền sở hữu -> 404)."""
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise NotFoundError("Không tìm thấy thông báo")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user: User) -> int:
    """Đánh dấu tất cả thông báo của người dùng là đã đọc."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user.id)
        .where(Notification.is_read.is_(False))
        .values(is_read=True)
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0
