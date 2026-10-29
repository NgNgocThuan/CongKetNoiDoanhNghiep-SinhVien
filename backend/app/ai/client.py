"""Provider-independent JSON completion with bounded retries and sanitized logs."""

import json
import time
from typing import Protocol

import httpx
from sqlalchemy.orm import Session

from app.ai.errors import LLMError
from app.ai.providers import Completion, build_request, read_completion
from app.core.config import settings
from app.core.enums import AIPurpose, AIRequestStatus
from app.models import AIRequestLog


class LLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict: ...


def _json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    result = json.loads(text)
    if not isinstance(result, dict):
        raise LLMError("Completion must be a JSON object")
    return result


class HTTPJSONClient:
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key: str,
        db: Session | None = None,
        purpose: AIPurpose = AIPurpose.OTHER,
        ref_type: str | None = None,
        ref_id: int | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        if provider not in {"gemini", "openai", "anthropic"}:
            raise LLMError("Unsupported AI_PROVIDER")
        if not model.strip() or not api_key.strip():
            raise LLMError("Configure AI_MODEL and AI_API_KEY before using AI")
        if max_retries < 0 or max_retries > 5 or timeout <= 0:
            raise ValueError("Invalid retry or timeout settings")
        self.provider, self.model, self.api_key = provider, model, api_key
        self.db, self.purpose, self.ref_type, self.ref_id = db, purpose, ref_type, ref_id
        self.transport, self.timeout, self.max_retries = transport, timeout, max_retries

    def _log(self, started: float, completion: Completion | None, error: str | None):
        if self.db is None:
            return
        self.db.add(
            AIRequestLog(
                purpose=self.purpose,
                ref_type=self.ref_type,
                ref_id=self.ref_id,
                provider=self.provider,
                model_name=self.model,
                input_tokens=completion.input_tokens if completion else None,
                output_tokens=completion.output_tokens if completion else None,
                status=AIRequestStatus.FAILED if error else AIRequestStatus.SUCCESS,
                error_message=error,
                latency_ms=int((time.monotonic() - started) * 1000),
            )
        )
        # The owning parser/service commits; never commit unrelated caller work here.
        self.db.flush()

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        url, headers, payload = build_request(
            self.provider, self.model, self.api_key, system_prompt, user_prompt
        )
        with httpx.Client(
            timeout=self.timeout, transport=self.transport, follow_redirects=False
        ) as client:
            for attempt in range(self.max_retries + 1):
                started, completion, error, retry = time.monotonic(), None, None, False
                try:
                    response = client.post(url, headers=headers, json=payload)
                    if response.is_error:
                        retry = response.status_code in {408, 429, 500, 502, 503, 504, 529}
                        raise LLMError(f"AI HTTP status {response.status_code}")
                    completion = read_completion(self.provider, response.json())
                    result = _json_object(completion.text)
                except httpx.TransportError:
                    error, retry = "AI transport failure", True
                except (ValueError, KeyError, IndexError, TypeError, AttributeError):
                    error = "Invalid AI response or JSON object"
                except LLMError as exc:
                    error = str(exc)
                self._log(started, completion, error)
                if error is None:
                    return result
                if not retry or attempt == self.max_retries:
                    raise LLMError(error) from None
                time.sleep(min(2**attempt, 4))
        raise LLMError("AI request failed")


def get_llm_client(
    *,
    db: Session | None = None,
    purpose: AIPurpose = AIPurpose.OTHER,
    ref_type: str | None = None,
    ref_id: int | None = None,
) -> LLMClient:
    return HTTPJSONClient(
        provider=settings.AI_PROVIDER,
        model=settings.AI_MODEL,
        api_key=settings.AI_API_KEY,
        db=db,
        purpose=purpose,
        ref_type=ref_type,
        ref_id=ref_id,
    )
