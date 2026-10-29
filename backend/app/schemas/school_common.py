"""Validated input shared by school-owned modules."""

from pydantic import BaseModel, ConfigDict, model_validator


class SchoolInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class SchoolUpdate(SchoolInput):
    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data):
        if isinstance(data, dict):
            required = getattr(cls, "required_non_null", ())
            for key in required:
                if key in data and data[key] is None:
                    raise ValueError(f"{key} không được để trống")
        return data
