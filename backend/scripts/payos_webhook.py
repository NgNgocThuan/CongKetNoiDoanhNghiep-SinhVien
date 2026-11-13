"""Explicit operator action: register the configured collection webhook.

Run only after deploying the API at PAYOS_WEBHOOK_URL. No money is moved.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.exceptions import AppException  # noqa: E402
from app.services.payos_gateway import PayOSGateway  # noqa: E402

if __name__ == "__main__":
    try:
        PayOSGateway().register_webhook()
        print("Collection webhook registered.")
    except AppException as exc:
        print(f"Registration failed: {exc.code}", file=sys.stderr)
        raise SystemExit(1) from None
