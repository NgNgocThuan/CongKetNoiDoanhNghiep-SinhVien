"""Gửi email tự động (ghi email_logs + gửi nền bằng FastAPI BackgroundTasks). Người phụ trách: TV1.

Hàm `queue_email` để các module khác gọi:

    email_service.queue_email(
        db, background_tasks,
        to_email=student.user.email, subject="Đơn ứng tuyển đã được ghi nhận",
        body_html="<p>...</p>", type="APPLY_SUCCESS", user_id=student.user_id,
        ref_type="APPLICATION", ref_id=application.id,
    )
"""
import html
from typing import Any, Optional

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import EmailStatus
from app.models import EmailLog
from app.schemas.common import PageParams
from app.tasks.email_tasks import send_email_task
from app.utils.pagination import paginate

# Cache nội dung HTML của email để retry chuẩn xác
_email_body_cache: dict[int, str] = {}


def queue_email(
    db: Session,
    background_tasks: BackgroundTasks,
    *,
    to_email: str,
    subject: str,
    body_html: str,
    type: str,
    user_id: Optional[int] = None,
    ref_type: Optional[str] = None,
    ref_id: Optional[int] = None,
) -> EmailLog:
    """Tạo bản ghi EmailLog và đưa tác vụ gửi email vào background_tasks."""
    log = EmailLog(
        user_id=user_id,
        recipient_email=to_email,
        type=type,
        subject=subject,
        ref_type=ref_type,
        ref_id=ref_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    _email_body_cache[log.id] = body_html
    # Truyền db vào send_email_task để tương thích với cả Test (SQLite in-memory) và Prod
    background_tasks.add_task(send_email_task, log.id, body_html, db)
    return log


def render_email_template(template_type: str, context: Optional[dict[str, Any]] = None) -> tuple[str, str]:
    """Sinh tiêu đề và nội dung HTML chuẩn cho các loại email thông báo (tự động escape XSS)."""
    ctx = context or {}
    frontend_url = settings.FRONTEND_URL.rstrip("/")

    def _esc(val: Any) -> str:
        if val is None:
            return ""
        return html.escape(str(val))

    if template_type == "PASSWORD_RESET":
        token = ctx.get("reset_token", "")
        expires = ctx.get("expires_minutes", settings.RESET_TOKEN_EXPIRE_MINUTES)
        link = f"{frontend_url}/reset-password?token={token}"
        subject = "[Student Connect] Yêu cầu đặt lại mật khẩu"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Yêu cầu đặt lại mật khẩu</h2>
            <p>Hệ thống nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.</p>
            <p>Vui lòng bấm vào liên kết dưới đây để đổi mật khẩu (liên kết có hiệu lực trong {_esc(expires)} phút):</p>
            <p><a href="{_esc(link)}" style="display: inline-block; padding: 10px 18px; background-color: #1677ff; color: #fff; text-decoration: none; border-radius: 4px;">Đặt lại mật khẩu</a></p>
            <p>Hoặc sao chép mã token sau: <code>{_esc(token)}</code></p>
            <p>Nếu bạn không gửi yêu cầu này, vui lòng bỏ qua email.</p>
        </div>
        """
        return subject, body_html.strip()

    if template_type == "ACCOUNT_ACTIVATION":
        token = ctx.get("activation_token", "")
        name = ctx.get("student_name", "Sinh viên")
        link = f"{frontend_url}/activate?token={token}"
        subject = "[Student Connect] Kích hoạt tài khoản sinh viên"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Chào mừng {_esc(name)} đến với Student Connect</h2>
            <p>Tài khoản sinh viên của bạn đã được khởi tạo bởi nhà trường.</p>
            <p>Vui lòng bấm vào liên kết dưới đây để kích hoạt tài khoản và thiết lập mật khẩu mới:</p>
            <p><a href="{_esc(link)}" style="display: inline-block; padding: 10px 18px; background-color: #52c41a; color: #fff; text-decoration: none; border-radius: 4px;">Kích hoạt tài khoản</a></p>
            <p>Mã token kích hoạt: <code>{_esc(token)}</code></p>
        </div>
        """
        return subject, body_html.strip()

    if template_type == "COMPANY_APPROVED":
        c_name = ctx.get("company_name", "Doanh nghiệp")
        subject = "[Student Connect] Hồ sơ doanh nghiệp đã được phê duyệt"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Chúc mừng {_esc(c_name)}</h2>
            <p>Hồ sơ đăng ký doanh nghiệp của bạn đã được nhà trường phê duyệt thành công.</p>
            <p>Bây giờ bạn đã có thể đăng nhập vào hệ thống, đăng tin tuyển dụng và kết nối với các ứng viên sinh viên tiềm năng.</p>
            <p><a href="{_esc(frontend_url)}/login" style="display: inline-block; padding: 10px 18px; background-color: #1677ff; color: #fff; text-decoration: none; border-radius: 4px;">Đăng nhập ngay</a></p>
        </div>
        """
        return subject, body_html.strip()

    if template_type == "COMPANY_REJECTED":
        c_name = ctx.get("company_name", "Doanh nghiệp")
        reason = ctx.get("reject_reason", "Chưa đáp ứng tiêu chí xác thực của nhà trường")
        subject = "[Student Connect] Thông báo về hồ sơ đăng ký doanh nghiệp"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Thông báo xét duyệt hồ sơ</h2>
            <p>Kính gửi {_esc(c_name)},</p>
            <p>Hồ sơ đăng ký của quý doanh nghiệp chưa được nhà trường phê duyệt với lý do:</p>
            <blockquote style="background: #f5f5f5; border-left: 4px solid #ff4d4f; padding: 10px; margin: 15px 0;">{_esc(reason)}</blockquote>
            <p>Vui lòng liên hệ bộ phận hỗ trợ nhà trường hoặc bổ sung hồ sơ để được xét duyệt lại.</p>
        </div>
        """
        return subject, body_html.strip()

    if template_type == "JOB_APPROVED":
        j_title = ctx.get("job_title", "Tin tuyển dụng")
        subject = f"[Student Connect] Tin tuyển dụng '{j_title}' đã được duyệt"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Tin tuyển dụng đã được phê duyệt</h2>
            <p>Tin tuyển dụng <strong>{_esc(j_title)}</strong> của bạn đã được nhà trường kiểm duyệt và đang hiển thị công khai cho sinh viên.</p>
        </div>
        """
        return subject, body_html.strip()

    if template_type == "JOB_REJECTED":
        j_title = ctx.get("job_title", "Tin tuyển dụng")
        reason = ctx.get("reject_reason", "Chưa phù hợp với quy định tuyển dụng")
        subject = f"[Student Connect] Tin tuyển dụng '{j_title}' chưa được duyệt"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Thông báo duyệt tin tuyển dụng</h2>
            <p>Tin tuyển dụng <strong>{_esc(j_title)}</strong> chưa được duyệt với lý do sau:</p>
            <blockquote style="background: #f5f5f5; border-left: 4px solid #ff4d4f; padding: 10px; margin: 15px 0;">{_esc(reason)}</blockquote>
            <p>Bạn có thể chỉnh sửa nội dung tin và gửi duyệt lại.</p>
        </div>
        """
        return subject, body_html.strip()

    if template_type == "ACCOUNT_LOCKED":
        reason = ctx.get("reason", "Vi phạm điều khoản sử dụng nền tảng")
        subject = "[Student Connect] Thông báo khóa tài khoản"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Tài khoản của bạn đã bị khóa</h2>
            <p>Quản trị viên đã tạm khóa quyền truy cập của tài khoản vì lý do:</p>
            <blockquote style="background: #f5f5f5; border-left: 4px solid #ff4d4f; padding: 10px; margin: 15px 0;">{_esc(reason)}</blockquote>
            <p>Vui lòng liên hệ quản trị viên nhà trường để được hỗ trợ mở khóa.</p>
        </div>
        """
        return subject, body_html.strip()

    if template_type == "ACCOUNT_UNLOCKED":
        subject = "[Student Connect] Thông báo mở khóa tài khoản"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Tài khoản của bạn đã được mở khóa</h2>
            <p>Quản trị viên đã mở khóa tài khoản của bạn. Bạn đã có thể tiếp tục đăng nhập và sử dụng hệ thống bình thường.</p>
            <p><a href="{_esc(frontend_url)}/login" style="display: inline-block; padding: 10px 18px; background-color: #1677ff; color: #fff; text-decoration: none; border-radius: 4px;">Đăng nhập</a></p>
        </div>
        """
        return subject, body_html.strip()

    if template_type == "REPORT_HANDLED":
        r_id = ctx.get("report_id", "")
        status = ctx.get("status", "")
        note = ctx.get("resolution_note", "Không có ghi chú")
        subject = f"[Student Connect] Báo cáo vi phạm #{r_id} đã được xử lý"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Kết quả xử lý báo cáo vi phạm #{_esc(r_id)}</h2>
            <p>Báo cáo của bạn đã được ban quản trị xem xét với kết quả: <strong>{_esc(status)}</strong>.</p>
            <p>Ghi chú xử lý: <em>{_esc(note)}</em></p>
            <p>Cảm ơn bạn đã đóng góp xây dựng môi trường lành mạnh cho Student Connect.</p>
        </div>
        """
        return subject, body_html.strip()

    # Mặc định
    subject = ctx.get("subject", "[Student Connect] Thông báo hệ thống")
    content = ctx.get("content", "Bạn có thông báo mới từ hệ thống Student Connect.")
    body_html = f"<div style='font-family: Arial, sans-serif;'><p>{_esc(content)}</p></div>"
    return subject, body_html


def retry_failed_emails(
    db: Session,
    background_tasks: BackgroundTasks,
    *,
    max_retries: int = 3,
    body_html_default: str = "<p>Thông báo từ hệ thống Student Connect.</p>",
) -> int:
    """Tìm các email FAILED có retry_count < max_retries và đưa vào hàng đợi gửi lại."""
    stmt = (
        select(EmailLog)
        .where(EmailLog.status == EmailStatus.FAILED)
        .where(EmailLog.retry_count < max_retries)
        .order_by(EmailLog.created_at.asc())
    )
    failed_logs = db.scalars(stmt).all()
    count = 0
    for log in failed_logs:
        log.status = EmailStatus.PENDING
        body_html = _email_body_cache.get(log.id) or body_html_default
        background_tasks.add_task(send_email_task, log.id, body_html, db)
        count += 1
    db.commit()
    return count


def list_email_logs(
    db: Session,
    params: PageParams,
    *,
    status: Optional[EmailStatus] = None,
    type: Optional[str] = None,
) -> dict:
    """Danh sách nhật ký email hệ thống có phân trang và bộ lọc."""
    stmt = select(EmailLog)
    if status:
        stmt = stmt.where(EmailLog.status == status)
    if type:
        stmt = stmt.where(EmailLog.type == type)
    stmt = stmt.order_by(EmailLog.created_at.desc(), EmailLog.id.desc())
    return paginate(db, stmt, params)
