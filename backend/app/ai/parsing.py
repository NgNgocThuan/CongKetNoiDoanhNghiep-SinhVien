"""Shared extraction validation and catalog integration, without domain writes."""

from pydantic import BaseModel, ValidationError

from app.ai.errors import LLMError
from app.services import catalog_service


class CatalogNotReadyError(LLMError):
    """TV2 has not supplied the agreed normalize_skill_names contract yet."""


def require_catalog_normalizer():
    normalize = getattr(catalog_service, "normalize_skill_names", None)
    if normalize is None:
        raise CatalogNotReadyError("TV2 must implement catalog_service.normalize_skill_names")
    return normalize


def normalize_skills(db, names: list[str]) -> list[str]:
    names = list(dict.fromkeys(name.strip() for name in names if name.strip()))
    if not names:
        return []
    skills = require_catalog_normalizer()(db, names)
    return list(dict.fromkeys(skill.name for skill in skills))


def validate_extraction(schema: type[BaseModel], payload: dict) -> dict:
    try:
        return schema.model_validate(payload).model_dump()
    except ValidationError:
        raise LLMError("AI extraction does not match the required schema") from None
