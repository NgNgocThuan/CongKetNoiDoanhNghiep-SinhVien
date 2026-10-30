"""CV extraction with content-addressed cache. Public signature belongs to TV3."""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.ai.client import LLMError, get_llm_client
from app.ai.contracts import CVExtraction
from app.ai.documents import extract_text, read_cv_file
from app.ai.parsing import normalize_skills, require_catalog_normalizer, validate_extraction
from app.ai.prompts import CV_PARSE_SYSTEM, PROMPT_VERSION
from app.core.enums import AIPurpose, CVType
from app.models import CV
from app.utils.datetime_utils import utcnow
from app.utils.hashing import sha256_bytes, sha256_json


def parse_cv(db: Session, cv: CV) -> dict:
    if cv.deleted_at is not None:
        raise LLMError("Cannot parse a deleted CV")
    if cv.type == CVType.ONLINE:
        source = json.dumps(cv.content_json or {}, sort_keys=True, ensure_ascii=False)
        digest = sha256_json([PROMPT_VERSION, cv.type, source])
        raw = None
    elif cv.type == CVType.UPLOADED and cv.file_url:
        raw = read_cv_file(cv.file_url)
        digest = sha256_json([PROMPT_VERSION, cv.type, sha256_bytes(raw)])
        source = ""
    else:
        raise LLMError("CV source is missing or unsupported")
    if cv.content_hash == digest and cv.parsed_json is not None:
        return cv.parsed_json
    if raw is not None:
        source = extract_text(raw, Path(cv.file_url).suffix)
    if not source.strip() or source == "{}" or len(source) > 100_000:
        raise LLMError("CV content is empty or exceeds AI input limit")
    require_catalog_normalizer()
    client = get_llm_client(db=db, purpose=AIPurpose.PARSE_CV, ref_type="cv", ref_id=cv.id)
    result = validate_extraction(CVExtraction, client.complete_json(CV_PARSE_SYSTEM, source))
    result["skills"] = normalize_skills(db, result["skills"])
    cv.extracted_text, cv.parsed_json = source, result
    cv.content_hash, cv.parsed_at = digest, utcnow()
    db.commit()
    return result
