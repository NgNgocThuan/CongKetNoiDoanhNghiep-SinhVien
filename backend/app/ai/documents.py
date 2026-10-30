"""Local CV text extraction. Never fetch arbitrary URLs supplied by a document."""

from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from app.ai.errors import LLMError
from app.core.config import settings
from app.utils.file_storage import absolute_path


def read_cv_file(file_url: str) -> bytes:
    root = Path(settings.UPLOAD_DIR).resolve()
    target = absolute_path(file_url).resolve()
    if not target.is_relative_to(root) or target.suffix.lower() not in {".pdf", ".docx"}:
        raise LLMError("Invalid local CV path")
    try:
        with target.open("rb") as source:
            data = source.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    except OSError:
        raise LLMError("CV file is unavailable") from None
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise LLMError("CV file exceeds upload size limit")
    return data


def extract_text(data: bytes, suffix: str) -> str:
    try:
        if suffix.lower() == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            with ZipFile(BytesIO(data)) as archive:
                info = archive.getinfo("word/document.xml")
                if info.file_size > 20 * 1024 * 1024:
                    raise LLMError("DOCX text exceeds extraction limit")
                root = ElementTree.fromstring(archive.read(info))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text = "\n".join("".join(p.itertext()) for p in root.findall(".//w:p", ns))
    except ImportError:
        raise LLMError("Install backend requirements to enable PDF extraction") from None
    except (ValueError, KeyError, BadZipFile, ElementTree.ParseError):
        raise LLMError("Unreadable CV document") from None
    if not text.strip():
        raise LLMError("CV contains no extractable text; scanned PDFs require OCR")
    if len(text) > 100_000:
        raise LLMError("CV text exceeds AI input limit")
    return text
