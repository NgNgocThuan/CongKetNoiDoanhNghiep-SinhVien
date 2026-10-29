"""Client gọi API NLP (GPT / Gemini / Claude). Người phụ trách: TV5.

Mục tiêu: các module khác chỉ làm việc với `LLMClient`, không biết provider cụ thể.
Provider chọn qua settings.AI_PROVIDER, key qua settings.AI_API_KEY.
"""
from typing import Protocol


class LLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Gửi prompt, ép trả về JSON và parse thành dict. Raise lỗi nếu JSON không hợp lệ."""
        ...


def get_llm_client() -> LLMClient:
    """TODO(TV5): trả về client theo settings.AI_PROVIDER (dùng httpx), có timeout + retry,
    ghi AIRequestLog (tokens, độ trễ, lỗi) cho mỗi lần gọi."""
    raise NotImplementedError
