from typing import Literal

from pydantic import BaseModel, StrictBool, field_validator

TERMS_VERSION = "2026-11-12"


class TermsAcceptance(BaseModel):
    accepted: StrictBool
    version: Literal["2026-11-12"]

    @field_validator("accepted")
    @classmethod
    def must_accept(cls, value):
        if not value:
            raise ValueError("Bạn cần đọc và đồng ý điều khoản để tiếp tục")
        return value
