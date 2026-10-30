"""HTTP wire formats for supported providers; no retries or persistence here."""

from dataclasses import dataclass
from urllib.parse import quote

from app.ai.errors import LLMError


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


def build_request(provider: str, model: str, key: str, system: str, user: str):
    if provider == "openai":
        return (
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {key}"},
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
            },
        )
    if provider == "anthropic":
        return (
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
            {
                "model": model,
                "max_tokens": 4096,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent",
        {"x-goog-api-key": key},
        {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        },
    )


def read_completion(provider: str, data: dict) -> Completion:
    if provider == "openai":
        choice = data["choices"][0]
        if choice["finish_reason"] != "stop":
            raise LLMError("Incomplete or refused completion")
        usage = data.get("usage", {})
        return Completion(
            choice["message"]["content"], usage.get("prompt_tokens"), usage.get("completion_tokens")
        )
    if provider == "anthropic":
        if data["stop_reason"] != "end_turn":
            raise LLMError("Incomplete or refused completion")
        text = "".join(part["text"] for part in data["content"] if part["type"] == "text")
        usage = data.get("usage", {})
        return Completion(text, usage.get("input_tokens"), usage.get("output_tokens"))
    candidate = data["candidates"][0]
    if candidate["finishReason"] != "STOP":
        raise LLMError("Incomplete or blocked completion")
    text = "".join(
        part.get("text", "") for part in candidate["content"]["parts"] if not part.get("thought")
    )
    usage = data.get("usageMetadata", {})
    return Completion(text, usage.get("promptTokenCount"), usage.get("candidatesTokenCount"))
