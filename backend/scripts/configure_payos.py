"""Initialize missing .env settings without printing secrets or replacing keys.

Run from backend: python scripts/configure_payos.py
This edits local configuration only; it does not contact payOS or migrate a DB.
"""

import re
import secrets
from pathlib import Path

from cryptography.fernet import Fernet


def initialize(root):
    env = root / ".env"
    sample = (root / ".env.example").read_text(encoding="utf-8")
    text = env.read_text(encoding="utf-8") if env.exists() else ""
    existing = dict(re.findall(r"^([A-Z][A-Z0-9_]*)\s*=([^\r\n]*)", text, re.MULTILINE))
    generated = {
        "FREELANCER_BANK_ENCRYPTION_KEY": lambda: Fernet.generate_key().decode(),
        "FREELANCER_BANK_FINGERPRINT_KEY": lambda: secrets.token_urlsafe(48),
    }
    additions = []
    for line in sample.splitlines():
        match = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", line)
        if not match:
            continue
        name, default = match.groups()
        if name in generated and not existing.get(name, "").strip().strip("\"'"):
            value = generated[name]()
            if name in existing:
                text = re.sub(rf"^{name}\s*=[^\r\n]*", f"{name}={value}", text, flags=re.MULTILINE)
            else:
                additions.append(f"{name}={value}")
        elif name not in existing:
            additions.append(line)
    if additions:
        text = (
            text.rstrip()
            + "\n\n# Added missing backend configuration\n"
            + "\n".join(additions)
            + "\n"
        )
    env.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    initialize(Path(__file__).resolve().parents[1])
    print(
        "Local .env prepared. Existing settings retained; fill payOS credentials and URLs before enabling channels."
    )
