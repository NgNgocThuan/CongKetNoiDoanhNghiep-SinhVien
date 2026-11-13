"""payOS wire protocol. No automatic POST retry and no database access.

Signatures follow payOSHQ/payos-lib-python 1.1.0; collection and payout
canonicalization are intentionally different. Credentials never enter errors.
"""

import hashlib
import hmac
import json
import re
from urllib.parse import quote, urlsplit

import httpx

from app.core.config import settings
from app.core.exceptions import AppException


class PayOSError(AppException):
    status_code = 503
    code = "PAYOS_UNAVAILABLE"

    def __init__(self, message="", *, code=None, diagnostics=None):
        super().__init__(message, code=code)
        self.diagnostics = diagnostics or {}


def _text(value):
    if value is None or value in ("null", "undefined"):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _sort(value):
    if isinstance(value, dict):
        return {key: _sort(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sort(item) for item in value]
    return value


def signature(data, secret, *, payout=False):
    pairs = []
    for key in sorted(data):
        value = data[key]
        if isinstance(value, (dict, list)):
            # Collection array objects sort only their immediate keys.
            if payout:
                value = _sort(value)
            elif isinstance(value, list):
                value = [dict(sorted(x.items())) if isinstance(x, dict) else x for x in value]
            value = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        else:
            value = _text(value)
        pairs.append(f"{quote(key) if payout else key}={quote(value) if payout else value}")
    return hmac.new(secret.encode(), "&".join(pairs).encode(), hashlib.sha256).hexdigest()


def validate_url(value, *, public=False):
    parsed = urlsplit(value)
    local = settings.is_development and parsed.hostname in ("localhost", "127.0.0.1")
    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
        or (parsed.scheme != "https" and not (local and not public))
    ):
        raise PayOSError("Configure a valid HTTPS URL", code="PAYOS_CONFIGURATION")
    return value.rstrip("/")


class PayOSGateway:
    def __init__(self, *, payout=False, transport=None):
        self.payout = payout
        prefix = "PAYOS_PAYOUT" if payout else "PAYOS_COLLECTION"
        self.client_id = getattr(settings, prefix + "_CLIENT_ID")
        self.api_key = getattr(settings, prefix + "_API_KEY")
        self.secret = getattr(settings, prefix + "_CHECKSUM_KEY")
        if not all((self.client_id, self.api_key, self.secret)):
            raise PayOSError("Configure all payOS channel credentials", code="PAYOS_CONFIGURATION")
        self.base = validate_url(settings.PAYOS_API_BASE_URL)
        self.transport = transport

    def error_details(self, response, envelope, body):
        # Persist only diagnostic fields; never whole responses or credentials.
        def clean(value):
            value = value if isinstance(value, str) else ""
            for secret in (self.client_id, self.api_key, self.secret,
                           (body or {}).get("toAccountNumber", "")):
                if secret:
                    value = value.replace(secret, "[redacted]")
            value = re.sub(r"\d{4,}", "[redacted]", value)
            return " ".join(value.split())[:400]
        return {"http_status": response.status_code,
                "provider_code": clean(envelope.get("code")),
                "provider_message": clean(envelope.get("desc"))}

    def request(self, method, path, *, body=None, params=None, key=None, signed=True):
        headers = {"x-client-id": self.client_id, "x-api-key": self.api_key}
        if self.payout and body is not None:
            headers["x-signature"] = signature(body, self.secret, payout=True)
        if key:
            headers["x-idempotency-key"] = key
        try:
            with httpx.Client(
                timeout=settings.PAYOS_TIMEOUT_SECONDS,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = client.request(
                    method, self.base + path, headers=headers, json=body, params=params
                )
            try:
                envelope = response.json()
            except ValueError:
                envelope = {}
            if not isinstance(envelope, dict):
                envelope = {}
            details = self.error_details(response, envelope, body)
            if not response.is_success:
                raise PayOSError("payOS HTTP request failed", code="PAYOS_HTTP_ERROR", diagnostics=details)
            if envelope.get("code") != "00":
                raise PayOSError("payOS did not confirm the request", code="PAYOS_NOT_CONFIRMED", diagnostics=details)
            if not isinstance(envelope.get("data"), dict):
                raise PayOSError("Invalid payOS response data", code="PAYOS_RESPONSE_INVALID", diagnostics=details)
            data = envelope["data"]
            if signed:
                supplied = (
                    response.headers.get("x-signature", "")
                    if self.payout
                    else envelope.get("signature", "")
                )
                if not isinstance(supplied, str) or not hmac.compare_digest(
                    signature(data, self.secret, payout=self.payout), supplied
                ):
                    raise PayOSError("Invalid payOS response signature", code="PAYOS_SIGNATURE")
            return data
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            # A failed/timeout POST has UNKNOWN outcome, never permission to re-create.
            raise PayOSError("payOS request outcome is not confirmed") from None

    def create_order(self, *, code, amount, expires):
        if not settings.PAYOS_COLLECTION_ENABLED:
            raise PayOSError("Collection channel is disabled", code="PAYOS_CONFIGURATION")
        body = {
            "orderCode": code,
            "amount": amount,
            "description": "SC" + str(code)[-7:],
            "cancelUrl": validate_url(settings.PAYOS_CANCEL_URL),
            "returnUrl": validate_url(settings.PAYOS_RETURN_URL),
        }
        body["signature"] = signature(body, self.secret)
        body["expiredAt"] = expires
        return self.request("POST", "/v2/payment-requests", body=body)

    def get_order(self, code):
        return self.request("GET", f"/v2/payment-requests/{int(code)}")

    def cancel_order(self, code):
        return self.request(
            "POST",
            f"/v2/payment-requests/{int(code)}/cancel",
            body={"cancellationReason": "Requested by payer"},
        )

    def register_webhook(self):
        return self.request(
            "POST",
            "/confirm-webhook",
            body={"webhookUrl": validate_url(settings.PAYOS_WEBHOOK_URL, public=True)},
            signed=False,
        )

    def create_payout(self, body, key):
        if not settings.PAYOS_PAYOUT_ENABLED:
            raise PayOSError("Payout channel is disabled", code="PAYOS_CONFIGURATION")
        return self.request("POST", "/v1/payouts", body=body, key=key)

    def find_payout(self, reference):
        return self.list_payouts(referenceId=reference, limit=100, offset=0)

    def list_payouts(self, **params):
        return self.request("GET", "/v1/payouts", params=params)

    def balance(self):
        return self.request("GET", "/v1/payouts-account/balance")


def verify_collection_webhook(envelope):
    gateway = PayOSGateway()
    data = envelope.get("data")
    supplied = envelope.get("signature")
    if (
        not isinstance(data, dict)
        or not isinstance(supplied, str)
        or not re.fullmatch(r"[0-9a-fA-F]{64}", supplied)
        or not hmac.compare_digest(signature(data, gateway.secret), supplied)
    ):
        raise AppException("Invalid webhook signature", code="PAYOS_SIGNATURE", status_code=401)
    if (
        data.get("code") != "00"
        or envelope.get("code") != "00"
        or envelope.get("success") is not True
    ):
        raise AppException("Not a successful payment event", code="PAYOS_EVENT_INVALID")
    return data
