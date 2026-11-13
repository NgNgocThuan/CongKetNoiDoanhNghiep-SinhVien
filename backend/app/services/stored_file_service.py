import hashlib
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import StoredFile
from app.services.freelancer_accounts.file_rules import (
    DOCUMENT_POLICY,
    FilePolicy,
    FileRejected,
    FileTypeRule,
    validate_upload,
)
from app.services.freelancer_domain import audit, event, lock, record, user

CATEGORIES = {
    "BUSINESS_LICENSE",
    "AUTHORIZATION",
    "MOU",
    "DELIVERABLE",
    "EVIDENCE",
    "CV",
    "PROJECT_REFERENCE",
}


def upload_in_tx(db, *, user_id, data, filename, mime, category):
    user(db, user_id, onboarding=True)
    if category not in CATEGORIES:
        raise BadRequestError("Invalid file category")
    policy = DOCUMENT_POLICY
    if category == "MOU":
        policy = FilePolicy("mou", 15 * 1024 * 1024, DOCUMENT_POLICY.rules)
    if category in ("DELIVERABLE", "CV", "PROJECT_REFERENCE"):
        policy = FilePolicy(
            "work",
            settings.MAX_UPLOAD_MB * 1024 * 1024,
            DOCUMENT_POLICY.rules
            + (
                FileTypeRule("zip", frozenset({"application/zip"}), (b"PK\x03\x04",)),
                FileTypeRule(
                    "docx",
                    frozenset(
                        {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
                    ),
                    (b"PK\x03\x04",),
                ),
                FileTypeRule(
                    "xlsx",
                    frozenset(
                        {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
                    ),
                    (b"PK\x03\x04",),
                ),
            ),
        )
    try:
        valid = validate_upload(
            policy, filename=filename, declared_mime=mime, head=data[:32], size=len(data)
        )
    except FileRejected as exc:
        raise BadRequestError(str(exc), code=exc.code) from None
    key = f"freelancer/{user_id}/{uuid4().hex}.{valid.extension}"
    root = Path(settings.UPLOAD_DIR).resolve()
    path = root / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    try:
        f = StoredFile(
            uploaded_by=user_id,
            storage_key=key,
            original_name=valid.safe_name,
            content_type=valid.mime_type,
            size_bytes=len(data),
            checksum_sha256=hashlib.sha256(data).hexdigest(),
            category=category,
            scan_status="PENDING" if settings.FREELANCER_FILE_SCAN_ENABLED else "CLEAN",
        )
        db.add(f)
        db.flush()
        if settings.FREELANCER_FILE_SCAN_ENABLED:
            event(db, f"file.scan:{f.id}", "file.scan", "stored_files", f.id, {"file_id": f.id})
        audit(
            db,
            user_id,
            "file.uploaded",
            "stored_files",
            f.id,
            after={"validation": "scanner" if settings.FREELANCER_FILE_SCAN_ENABLED else "format"},
        )
        return record(f, exclude=("storage_key",))
    except Exception:
        path.unlink(missing_ok=True)
        raise


def get_file(db, *, user_id, file_id):
    user(db, user_id, onboarding=True)
    f = db.get(StoredFile, file_id)
    if not f or f.uploaded_by != user_id:
        raise NotFoundError("File not found")
    return record(f, exclude=("storage_key",))


def scan_outside_tx(db, file_id):
    from app.services.freelancer_adapters import scan_file

    f = db.get(StoredFile, file_id)
    if not f:
        raise NotFoundError("File not found")
    if f.scan_status != "PENDING":
        return f.scan_status
    key, checksum, size = f.storage_key, f.checksum_sha256, f.size_bytes
    db.rollback()
    root = Path(settings.UPLOAD_DIR).resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise NotFoundError("File content missing")
    data = path.read_bytes()
    if len(data) != size or hashlib.sha256(data).hexdigest() != checksum:
        raise ConflictError("Stored file integrity check failed")
    verdict = scan_file(path, checksum)
    f = lock(db, StoredFile, id=file_id)
    if f.checksum_sha256 != checksum or f.storage_key != key:
        raise ConflictError("File changed during scanning")
    if f.scan_status == "PENDING":
        f.scan_status = verdict
        if verdict == "REJECTED":
            f.availability_status = "QUARANTINED"
        audit(db, None, "file.scanned", "stored_files", f.id, after={"verdict": verdict})
    return verdict
