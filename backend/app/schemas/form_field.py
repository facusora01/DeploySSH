from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, field_validator


FieldType = Literal["text", "yes_no", "select"]


class FormFieldCreate(BaseModel):
    field_name: str
    is_required: bool = False
    order: int = 0
    field_type: FieldType = "text"
    options: list[str] = []


class FormFieldUpdate(BaseModel):
    field_name: Optional[str] = None
    is_required: Optional[bool] = None
    order: Optional[int] = None
    field_type: Optional[FieldType] = None
    options: Optional[list[str]] = None


class FormFieldOut(BaseModel):
    id: UUID
    field_name: str
    is_required: bool
    order: int
    field_type: str
    options: list[str] = []

    @field_validator("options", mode="before")
    @classmethod
    def coerce_options(cls, v: object) -> list[str]:
        if v is None:
            return []
        return v

    model_config = ConfigDict(from_attributes=True)


class FormFieldAnswerCreate(BaseModel):
    field_id: UUID
    answer: str


class FormFieldAnswerOut(BaseModel):
    field_id: UUID
    field_name: str
    answer: str

    model_config = ConfigDict(from_attributes=True)
