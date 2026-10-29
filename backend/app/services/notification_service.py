"""Thông báo trong ứng dụng. Người phụ trách: TV1.

Hàm `create_notification` ĐÃ CÓ BẢN CƠ BẢN để các module khác gọi ngay
(duyệt doanh nghiệp/tin, đổi trạng thái đơn, lời mời, kết quả thực tập...).
TV1 bổ sung: list_notifications, unread_count, mark_read, mark_all_read.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Notification


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
        user_id=user_id, type=type, title=title, content=content, ref_type=ref_type, ref_id=ref_id
    )
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    else:
        db.flush()
    return notification


# TODO(TV1): list_notifications(db, user, params), unread_count(db, user), mark_read, mark_all_read
