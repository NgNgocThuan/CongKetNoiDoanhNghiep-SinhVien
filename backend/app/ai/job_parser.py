"""Job extraction with validated output and content-addressed cache."""

import json

from sqlalchemy.orm import Session

from app.ai.client import LLMError, get_llm_client
from app.ai.contracts import JobExtraction
from app.ai.parsing import normalize_skills, require_catalog_normalizer, validate_extraction
from app.ai.prompts import JOB_PARSE_SYSTEM, PROMPT_VERSION
from app.core.enums import AIPurpose
from app.models import Job
from app.utils.datetime_utils import utcnow
from app.utils.hashing import sha256_json


def parse_job(db: Session, job: Job) -> dict:
    source = {
        name: getattr(job, name) for name in ("title", "position", "description", "requirements")
    }
    digest = sha256_json([PROMPT_VERSION, source])
    if job.content_hash == digest and job.parsed_json is not None:
        return job.parsed_json
    text = json.dumps(source, sort_keys=True, ensure_ascii=False)
    if len(text) > 100_000:
        raise LLMError("Job text exceeds AI input limit")
    require_catalog_normalizer()
    client = get_llm_client(db=db, purpose=AIPurpose.PARSE_JOB, ref_type="job", ref_id=job.id)
    result = validate_extraction(JobExtraction, client.complete_json(JOB_PARSE_SYSTEM, text))
    for field in ("required_skills", "preferred_skills"):
        result[field] = normalize_skills(db, result[field])
    job.parsed_json, job.content_hash, job.parsed_at = result, digest, utcnow()
    db.commit()
    return result
