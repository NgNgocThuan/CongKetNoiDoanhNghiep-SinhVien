"""Encrypted, self-declared payout destinations and atomic resumption of waiting payouts."""

import hashlib
import hmac
import re

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import AppException, BadRequestError, ConflictError
from app.models import BankDestination, MoneyTransfer
from app.services.freelancer_domain import audit, event, lock, notify, user

USABLE = ("ACTIVE", "VERIFIED")


def cipher():
    try:
        return Fernet(settings.FREELANCER_BANK_ENCRYPTION_KEY.encode())
    except (ValueError, TypeError):
        raise AppException(
            "Configure the bank encryption key", code="BANK_CONFIGURATION", status_code=503
        ) from None


def public_destination(row):
    return {
        "id": str(row.id),
        "user_id": str(row.user_id),
        "bank_bin": row.bank_bin,
        "account_last4": row.account_last4,
        "account_name": row.account_name,
        "verification_status": str(row.verification_status),
        "status_label": "Đang sử dụng" if row.verification_status in USABLE else "Ngừng sử dụng" if row.verification_status == "DISABLED" else "Không khả dụng",
        "verification_source": row.verification_source,
    }


def add_in_tx(db, *, user_id, bank_bin, account_number, account_name):
    user(db, user_id)
    if not re.fullmatch(r"\d{6}", bank_bin) or not re.fullmatch(r"\d{4,30}", account_number):
        raise AppException("Invalid bank BIN or account number")
    from app.services.bank_catalog import banks as bank_catalog
    if not any(bank["bin"] == bank_bin for bank in bank_catalog()):
        raise BadRequestError("Ngân hàng không nằm trong danh mục hỗ trợ")
    account_name = account_name.strip()
    if not 2 <= len(account_name) <= 255:
        raise BadRequestError("Tên chủ tài khoản phải có từ 2 đến 255 ký tự")
    secret = settings.FREELANCER_BANK_FINGERPRINT_KEY
    if len(secret) < 32:
        raise AppException(
            "Configure a separate bank fingerprint key", code="BANK_CONFIGURATION", status_code=503
        )
    fingerprint = hmac.new(
        secret.encode(), f"{bank_bin}:{account_number}".encode(), hashlib.sha256
    ).hexdigest()
    old = lock(
        db, BankDestination, user_id=user_id, bank_bin=bank_bin, account_fingerprint=fingerprint
    )
    if old:
        if old.verification_status not in USABLE:
            raise ConflictError("Tài khoản đã bị ngừng sử dụng hoặc không khả dụng. Vui lòng thêm tài khoản khác.")
        resume_waiting_in_tx(db, user_id=user_id, destination=old)
        return public_destination(old)
    row = BankDestination(
        user_id=user_id,
        bank_bin=bank_bin,
        account_number_ciphertext=cipher().encrypt(account_number.encode()).decode(),
        account_fingerprint=fingerprint,
        account_last4=account_number[-4:],
        account_name=account_name.strip(),
        verification_status="ACTIVE",
        verification_source="SELF_DECLARED",
        encryption_key_version=settings.FREELANCER_BANK_KEY_VERSION,
    )
    db.add(row)
    db.flush()
    audit(db, user_id, "bank_destination.created", "bank_destinations", row.id)
    resume_waiting_in_tx(db, user_id=user_id, destination=row)
    return public_destination(row)


def destination(db, user_id, *, required=True):
    rows = db.scalars(
        select(BankDestination)
        .where(
            BankDestination.user_id == user_id, BankDestination.verification_status.in_(USABLE)
        )
        .order_by(BankDestination.id.desc())
        .with_for_update()
    ).all()
    if not rows:
        if not required:
            return None
        raise ConflictError(
            "Vui lòng bổ sung tài khoản ngân hàng để nhận tiền", code="BANK_DESTINATION_REQUIRED"
        )
    return rows[0]


def resume_waiting_in_tx(db, *, user_id, destination):
    """Attach bank details only to never-sent transfers, preserving their original references."""
    waiting = db.scalars(select(MoneyTransfer).where(
        MoneyTransfer.recipient_user_id == user_id,
        MoneyTransfer.status == "WAITING_BANK",
    ).order_by(MoneyTransfer.id).with_for_update()).all()
    for transfer in waiting:
        transfer.destination_id = destination.id
        transfer.destination_snapshot = snapshot(destination)
        transfer.status = "READY"
        event(db, f"transfer:{transfer.id}:send", "finance.transfer", "money_transfers",
              transfer.id, {"transfer_id": transfer.id})
        audit(db, user_id, "transfer.bank_added", "money_transfers", transfer.id)
    if waiting:
        notify(db, user_id, "Đã tiếp tục xử lý chi trả",
               f"Đã bổ sung tài khoản nhận tiền. {len(waiting)} lệnh giải ngân/hoàn tiền đang chờ sẽ được hệ thống tự động xử lý.",
               ref_type="BANK_DESTINATION", ref_id=destination.id)
    return len(waiting)


def snapshot(row):
    return {
        "bank_bin": row.bank_bin,
        "account_number_ciphertext": row.account_number_ciphertext,
        "account_last4": row.account_last4,
        "account_name": row.account_name,
        "encryption_key_version": row.encryption_key_version,
    }


def decrypt_snapshot(data):
    if data["encryption_key_version"] != settings.FREELANCER_BANK_KEY_VERSION:
        raise AppException(
            "Bank encryption key version unavailable", code="BANK_CONFIGURATION", status_code=503
        )
    try:
        return cipher().decrypt(data["account_number_ciphertext"].encode()).decode()
    except InvalidToken:
        raise AppException(
            "Bank decryption failed", code="BANK_CONFIGURATION", status_code=503
        ) from None
