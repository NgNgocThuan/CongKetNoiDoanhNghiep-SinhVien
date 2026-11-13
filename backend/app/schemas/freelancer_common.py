"""JSON-safe integer scalar types for new Freelancer endpoints only."""
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, PlainSerializer


def _integer(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and value.isascii() and value.isdigit():
        return int(value)
    raise ValueError("Expected an integer or a decimal integer string")


def _money(value: int) -> int:
    if not 0 <= value <= 2**63 - 1:
        raise ValueError("VND amount exceeds BIGINT range")
    return value


def _escrow_money(value: int) -> int:
    if value <= 2000:
        raise ValueError("Escrow amount must be greater than 2,000 VND")
    return value


def _id(value: int) -> int:
    if not 0 < value <= 2**64 - 1:
        raise ValueError("ID must be a positive unsigned BIGINT")
    return value


MoneyVnd = Annotated[
    int, BeforeValidator(_integer), AfterValidator(_money),
    PlainSerializer(str, return_type=str, when_used="json"),
]
EscrowMoneyVnd = Annotated[
    int, BeforeValidator(_integer), AfterValidator(_money), AfterValidator(_escrow_money),
    PlainSerializer(str, return_type=str, when_used="json"),
]
EntityId = Annotated[
    int, BeforeValidator(_integer), AfterValidator(_id),
    PlainSerializer(str, return_type=str, when_used="json"),
]
