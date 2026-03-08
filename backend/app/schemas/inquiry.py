import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class InquiryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    age: int = Field(ge=18, le=30)
    preferred_date: str = Field(alias="preferredDate")
    plan: str = Field(min_length=1, max_length=50)
    message: str = Field(default="", max_length=2000)
    model_config = {"populate_by_name": True}

    @field_validator("phone")
    @classmethod
    def validate_japanese_phone(cls, v: str) -> str:
        cleaned: str = re.sub(r"[\s\-()]", "", v)
        patterns: list[str] = [r"^0[6-9]0\d{8}$", r"^\+?81[6-9]0\d{8}$", r"^0\d{9,10}$"]
        if not any(re.match(p, cleaned) for p in patterns):
            raise ValueError("有効な電話番号を入力してください")
        return v


class InquiryResponse(BaseModel):
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


class InquiryCreateResponse(BaseModel):
    success: bool = True
    message: str
    inquiry: InquiryResponse


class InquiryStatusUpdateResponse(BaseModel):
    success: bool = True
    message: str
    inquiry: InquiryResponse


class InquiryListResponse(BaseModel):
    success: bool = True
    inquiries: list[InquiryResponse]
    count: int


class InquiryStatusUpdate(BaseModel):
    status: Literal["pending", "contacted", "completed"]
    admin_note: str | None = None
