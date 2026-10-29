from io import BytesIO
from types import SimpleNamespace as NS
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from app.ai import cv_parser, job_parser
from app.ai.client import LLMError
from app.ai.documents import extract_text, read_cv_file
from app.ai.parsing import CatalogNotReadyError, normalize_skills


@pytest.fixture()
def extraction(monkeypatch):
    normalize = Mock(side_effect=lambda db, names: [NS(name="Python")] if names else [])
    monkeypatch.setattr(
        "app.ai.parsing.catalog_service.normalize_skill_names", normalize, raising=False
    )
    return normalize


def test_online_cv_cache_and_content_changes(monkeypatch, extraction):
    result = {
        "skills": ["py"],
        "experience_months": 6,
        "projects": [],
        "domains": [],
        "keywords": [],
    }
    client = NS(complete_json=Mock(return_value=result))
    monkeypatch.setattr(cv_parser, "get_llm_client", lambda **kwargs: client)
    cv = NS(
        id=1,
        type="ONLINE",
        deleted_at=None,
        content_json={"bio": "Python"},
        content_hash=None,
        parsed_json=None,
    )
    db = Mock()
    assert cv_parser.parse_cv(db, cv)["skills"] == ["Python"]
    assert cv_parser.parse_cv(db, cv)["experience_months"] == 6
    assert client.complete_json.call_count == 1
    cv.content_json["bio"] = "Changed"
    cv_parser.parse_cv(db, cv)
    assert client.complete_json.call_count == 2
    assert db.commit.call_count == 2


def test_job_cache_and_position_invalidation(monkeypatch, extraction):
    result = {
        "required_skills": ["py"],
        "preferred_skills": [],
        "min_experience_months": 0,
        "education": None,
        "domains": [],
        "keywords": [],
    }
    client = NS(complete_json=Mock(return_value=result))
    monkeypatch.setattr(job_parser, "get_llm_client", lambda **kwargs: client)
    job = NS(
        id=1,
        title="Dev",
        position="Intern",
        description="Python",
        requirements=None,
        content_hash=None,
        parsed_json=None,
    )
    db = Mock()
    assert job_parser.parse_job(db, job)["required_skills"] == ["Python"]
    job_parser.parse_job(db, job)
    assert client.complete_json.call_count == 1
    job.position = "Junior"
    job_parser.parse_job(db, job)
    assert client.complete_json.call_count == 2


def test_invalid_extraction_does_not_replace_cache(monkeypatch, extraction):
    monkeypatch.setattr(
        cv_parser, "get_llm_client", lambda **kwargs: NS(complete_json=lambda *args: {"score": 100})
    )
    cv = NS(
        id=1,
        type="ONLINE",
        deleted_at=None,
        content_json={"bio": "new"},
        content_hash="old",
        parsed_json={"old": True},
    )
    db = Mock()
    with pytest.raises(LLMError, match="schema"):
        cv_parser.parse_cv(db, cv)
    assert cv.content_hash == "old"
    assert cv.parsed_json == {"old": True}
    db.commit.assert_not_called()


def test_catalog_dependency_is_explicit(monkeypatch):
    monkeypatch.delattr("app.ai.parsing.catalog_service.normalize_skill_names", raising=False)
    with pytest.raises(CatalogNotReadyError):
        normalize_skills(Mock(), ["Python"])


def test_docx_text_extraction():
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Python developer</w:t></w:r></w:p></w:body></w:document>',
        )
    assert extract_text(buffer.getvalue(), ".docx") == "Python developer"


def test_path_escape_rejected():
    with pytest.raises(LLMError, match="path"):
        read_cv_file("../private.pdf")


def test_uploaded_cache_uses_bytes_not_extracted_text(monkeypatch, extraction):
    result = {"skills": [], "experience_months": 0, "projects": [], "domains": [], "keywords": []}
    client = NS(complete_json=Mock(return_value=result))
    monkeypatch.setattr(cv_parser, "get_llm_client", lambda **kwargs: client)
    source = {"bytes": b"first file"}
    monkeypatch.setattr(cv_parser, "read_cv_file", lambda _: source["bytes"])
    extract = Mock(return_value="Python developer")
    monkeypatch.setattr(cv_parser, "extract_text", extract)
    cv = NS(
        id=1,
        type="UPLOADED",
        deleted_at=None,
        file_url="cvs/test.pdf",
        content_hash=None,
        parsed_json=None,
    )
    db = Mock()
    cv_parser.parse_cv(db, cv)
    cv_parser.parse_cv(db, cv)
    assert extract.call_count == client.complete_json.call_count == 1
    source["bytes"] = b"changed file"
    cv_parser.parse_cv(db, cv)
    assert client.complete_json.call_count == 2


def test_missing_catalog_fails_before_paid_request(monkeypatch):
    monkeypatch.delattr("app.ai.parsing.catalog_service.normalize_skill_names", raising=False)
    factory = Mock()
    monkeypatch.setattr(cv_parser, "get_llm_client", factory)
    cv = NS(
        id=1,
        type="ONLINE",
        deleted_at=None,
        content_json={"bio": "new"},
        content_hash=None,
        parsed_json=None,
    )
    with pytest.raises(CatalogNotReadyError):
        cv_parser.parse_cv(Mock(), cv)
    factory.assert_not_called()


def test_pdf_text_extraction():
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 10 100 Td (Python developer) Tj ET")
    page[NameObject("/Contents")] = content
    buffer = BytesIO()
    writer.write(buffer)
    assert "Python developer" in extract_text(buffer.getvalue(), ".pdf")
