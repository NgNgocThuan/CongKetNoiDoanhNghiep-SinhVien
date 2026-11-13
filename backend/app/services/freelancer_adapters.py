"""Configurable HTTPS gateway contracts; not tied to an unapproved vendor."""

import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.core.exceptions import AppException


def _url(value):
    if not value:
        raise AppException("Provider not configured", code="PROVIDER_UNAVAILABLE", status_code=503)
    parsed = urlsplit(value)
    if parsed.scheme != "https" and not (
        settings.is_development
        and parsed.scheme == "http"
        and parsed.hostname in ("127.0.0.1", "localhost")
    ):
        raise AppException("Provider must use HTTPS", code="PROVIDER_UNAVAILABLE", status_code=503)
    if parsed.username or parsed.password:
        raise AppException("Credentials must be configured separately", status_code=503)
    return value


def scan_file(path, checksum):
    if not settings.FREELANCER_SCAN_GATEWAY_URL and settings.is_development:
        return _scan_with_windows_defender(path)
    url = _url(settings.FREELANCER_SCAN_GATEWAY_URL)
    try:
        with httpx.Client(timeout=45, follow_redirects=False) as client, path.open("rb") as stream:
            response = client.post(
                url,
                headers={"Authorization": "Bearer " + settings.FREELANCER_SCAN_GATEWAY_TOKEN},
                files={"file": (path.name, stream, "application/octet-stream")},
                data={"sha256": checksum},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("sha256") != checksum or data.get("verdict") not in ("CLEAN", "REJECTED"):
                raise ValueError("Invalid scan response")
            return data["verdict"]
    except Exception:
        raise AppException(
            "File scanner unavailable", code="SCANNER_NOT_READY", status_code=503
        ) from None


def _scan_with_windows_defender(path):
    """Use the host antivirus for local development without faking a clean verdict."""
    program_files = Path(os.environ.get("ProgramFiles", ""))
    executable = program_files / "Windows Defender" / "MpCmdRun.exe"
    if not executable.is_file():
        raise AppException(
            "Local Windows Defender scanner is unavailable",
            code="SCANNER_NOT_READY",
            status_code=503,
        )
    try:
        result = subprocess.run(
            [
                str(executable),
                "-Scan",
                "-ScanType",
                "3",
                "-File",
                str(path),
                "-DisableRemediation",
            ],
            check=False,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        raise AppException(
            "Local file scanner failed", code="SCANNER_NOT_READY", status_code=503
        ) from None
    if result.returncode == 0:
        return "CLEAN"
    # A nonzero result is never treated as clean. Keep the file unavailable
    # until an operator can distinguish a detection from a scanner failure.
    raise AppException(
        "Local file scan did not return a clean verdict",
        code="SCANNER_NOT_READY",
        status_code=503,
    )
