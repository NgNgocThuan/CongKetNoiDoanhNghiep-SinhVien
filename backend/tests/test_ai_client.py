import json

import httpx
import pytest
from sqlalchemy import select

from app.ai.client import HTTPJSONClient, LLMError
from app.models import AIRequestLog


@pytest.mark.parametrize(
    "provider,payload",
    [
        (
            "openai",
            {
                "choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 3},
            },
        ),
        (
            "anthropic",
            {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": '{"ok":true}'}],
                "usage": {"input_tokens": 10, "output_tokens": 3},
            },
        ),
        (
            "gemini",
            {
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": '{"ok":true}'}]}}
                ],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 3},
            },
        ),
    ],
)
def test_provider_contracts_and_usage(db, provider, payload):
    def handler(request):
        body = json.loads(request.content)
        assert "system secret" in str(body)
        return httpx.Response(200, json=payload)

    client = HTTPJSONClient(
        provider=provider,
        model="test",
        api_key="key",
        db=db,
        transport=httpx.MockTransport(handler),
    )
    assert client.complete_json("system secret", "private CV") == {"ok": True}
    log = db.scalars(select(AIRequestLog)).one()
    assert (log.input_tokens, log.output_tokens, log.status) == (10, 3, "SUCCESS")
    assert log.error_message is None


@pytest.mark.parametrize("status,expected_calls", [(429, 3), (503, 3), (401, 1)])
def test_retry_and_safe_logs(db, monkeypatch, status, expected_calls):
    monkeypatch.setattr("app.ai.client.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, text="private CV and key")

    client = HTTPJSONClient(
        provider="openai",
        model="test",
        api_key="key",
        db=db,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(LLMError, match=f"AI HTTP status {status}"):
        client.complete_json("system", "private CV")
    assert len(calls) == expected_calls
    logs = db.scalars(select(AIRequestLog)).all()
    assert len(logs) == expected_calls
    assert all("private" not in log.error_message for log in logs)


@pytest.mark.parametrize("content", ["not json", "[]", "null"])
def test_invalid_json_not_retried(content):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200, json={"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
        )

    client = HTTPJSONClient(
        provider="openai", model="test", api_key="key", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(LLMError):
        client.complete_json("system", "CV")
    assert len(calls) == 1


def test_transport_retry_recovers(monkeypatch):
    monkeypatch.setattr("app.ai.client.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            raise httpx.ReadTimeout("private data", request=request)
        return httpx.Response(
            200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
        )

    client = HTTPJSONClient(
        provider="openai", model="test", api_key="key", transport=httpx.MockTransport(handler)
    )
    assert client.complete_json("system", "CV") == {}
    assert len(calls) == 2


def test_truncated_completion_rejected():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}
        )
    )
    client = HTTPJSONClient(provider="openai", model="test", api_key="key", transport=transport)
    with pytest.raises(LLMError, match="Incomplete"):
        client.complete_json("system", "CV")
