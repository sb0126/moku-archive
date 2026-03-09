import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import CamelModel


class InquiryCreate(CamelModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    age: int = Field(ge=18, le=30)
    preferred_date: str = Field(alias="preferredDate")
    plan: str = Field(min_length=1, max_length=50)
    message: str = Field(default="", max_length=2000)

    @field_validator("phone")
    @classmethod
    def validate_japanese_phone(cls, v: str) -> str:
        cleaned: str = re.sub(r"[\s\-()]", "", v)
        patterns: list[str] = [r"^0[6-9]0\d{8}$", r"^\+?81[6-9]0\d{8}$", r"^0\d{9,10}$"]
        if not any(re.match(p, cleaned) for p in patterns):
            raise ValueError("有効な電話番号を入力してください")
        return v


class InquiryResponse(CamelModel):
    id: str
    name: str
    email: str
    phone: str
    age: int
    preferred_date: str | None
    plan: str | None
    message: str
    status: str
    admin_note: str | None
    created_at: datetime
    updated_at: datetime


class InquiryCreateResponse(CamelModel):
    success: bool = True
    message: str
    inquiry: InquiryResponse


class InquiryStatusUpdateResponse(CamelModel):
    success: bool = True
    message: str
    inquiry: InquiryResponse


class InquiryListResponse(CamelModel):
    success: bool = True
    inquiries: list[InquiryResponse]
    count: int


class InquiryStatusUpdate(CamelModel):
    status: Literal["pending", "contacted", "completed"]
    admin_note: str | None = None

