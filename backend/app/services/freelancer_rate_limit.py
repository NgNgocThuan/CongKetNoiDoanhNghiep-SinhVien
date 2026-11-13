"""Database-backed abuse counters, fixed windows, HMAC scopes and stable lock order."""

import hashlib
import hmac
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.exceptions import AppException
from app.models import OtpRateBucket
from app.services.freelancer_domain import lock


def consume_in_tx(db, *, scopes, at):
    values = []
    for scope, limit, seconds in scopes:
        hashed = hmac.new(settings.SECRET_KEY.encode(), scope.encode(), hashlib.sha256).hexdigest()
        values.append((hashed, limit, seconds))
    for hashed, limit, seconds in sorted(values):
        row = db.scalar(
            select(OtpRateBucket).where(OtpRateBucket.scope_hash == hashed).with_for_update()
        )
        if row is None:
            try:
                with db.begin_nested():
                    row = OtpRateBucket(scope_hash=hashed, window_started_at=at, count=0)
                    db.add(row)
                    db.flush()
            except IntegrityError:
                row = lock(db, OtpRateBucket, scope_hash=hashed)
        if at >= row.window_started_at + timedelta(seconds=seconds):
            row.window_started_at = at
            row.count = 0
        if row.count >= limit:
            raise AppException("Request rate limit reached", code="RATE_LIMITED", status_code=429)
        row.count += 1
    db.flush()
