"""Test toàn diện phân hệ Thông báo & Email. Người phụ trách: TV1."""
from fastapi import BackgroundTasks

from app.core.enums import EmailStatus, UserRole
from app.models import EmailLog
from app.services import email_service, notification_service


def test_list_notifications_and_unread_count(client, make_user, auth_headers, db):
    user = make_user(UserRole.STUDENT, email="noti_user@test.com")
    headers = auth_headers(user)

    # Ban đầu chưa có thông báo
    res_count_0 = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res_count_0.status_code == 200
    assert res_count_0.json()["unread_count"] == 0

    # Tạo 2 thông báo chưa đọc và 1 thông báo đã đọc
    notification_service.create_notification(
        db, user_id=user.id, type="TEST_1", title="Thông báo 1", content="Nội dung 1"
    )
    notification_service.create_notification(
        db, user_id=user.id, type="TEST_2", title="Thông báo 2", content="Nội dung 2"
    )
    n3 = notification_service.create_notification(
        db, user_id=user.id, type="TEST_3", title="Thông báo 3", content="Nội dung 3"
    )
    n3.is_read = True
    db.commit()

    # Đếm số chưa đọc -> 2
    res_count = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res_count.status_code == 200
    assert res_count.json()["unread_count"] == 2

    # Lấy danh sách tất cả -> 3
    res_list = client.get("/api/v1/notifications", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 3

    # Lọc chỉ lấy chưa đọc -> 2
    res_unread = client.get("/api/v1/notifications?is_read=false", headers=headers)
    assert res_unread.status_code == 200
    assert res_unread.json()["total"] == 2


def test_mark_read_and_security_ownership(client, make_user, auth_headers, db):
    user_a = make_user(UserRole.STUDENT, email="user_a@test.com")
    user_b = make_user(UserRole.STUDENT, email="user_b@test.com")

    n_a = notification_service.create_notification(
        db, user_id=user_a.id, type="MSG_A", title="Tin của A"
    )
    n_b = notification_service.create_notification(
        db, user_id=user_b.id, type="MSG_B", title="Tin của B"
    )

    headers_a = auth_headers(user_a)

    # User A đánh dấu đọc thông báo của chính mình -> 200
    res_read_own = client.post(f"/api/v1/notifications/{n_a.id}/read", headers=headers_a)
    assert res_read_own.status_code == 200
    assert res_read_own.json()["is_read"] is True

    # User A cố tình đọc thông báo của User B -> Bắt buộc trả 404 (chống thăm dò ID)
    res_read_other = client.post(f"/api/v1/notifications/{n_b.id}/read", headers=headers_a)
    assert res_read_other.status_code == 404


def test_mark_all_read(client, make_user, auth_headers, db):
    user = make_user(UserRole.STUDENT, email="mark_all@test.com")
    headers = auth_headers(user)

    for i in range(4):
        notification_service.create_notification(
            db, user_id=user.id, type="BATCH", title=f"Tin {i}"
        )

    res_all = client.post("/api/v1/notifications/read-all", headers=headers)
    assert res_all.status_code == 200
    assert res_all.json()["updated_count"] == 4

    res_count = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res_count.json()["unread_count"] == 0


def test_retry_failed_emails(db):
    bg_tasks = BackgroundTasks()

    log_failed = EmailLog(
        recipient_email="retry_test@test.com",
        type="TEST",
        subject="Retry Test",
        status=EmailStatus.FAILED,
        retry_count=1,
    )
    db.add(log_failed)
    db.commit()

    count = email_service.retry_failed_emails(db, bg_tasks, max_retries=3)
    assert count == 1
    assert log_failed.status == EmailStatus.PENDING
