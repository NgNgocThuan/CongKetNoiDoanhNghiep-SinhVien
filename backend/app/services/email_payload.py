"""Encrypted email retry payloads; no process-local cache or plaintext token storage."""
import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _cipher():
    key = hashlib.sha256(("student-connect:email:v1:" + settings.SECRET_KEY).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_body(body: str) -> str:
    return _cipher().encrypt(body.encode("utf-8")).decode("ascii")


def decrypt_body(payload: str) -> str:
    return _cipher().decrypt(payload.encode("ascii")).decode("utf-8")
