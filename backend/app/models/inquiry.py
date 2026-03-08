"""Inquiry table model."""

from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, Optional

from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now — replaces deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


class InquiryStatus(str, Enum):
    """Allowed values for Inquiry.status."""

    PENDING = "pending"
    CONTACTED = "contacted"
    COMPLETED = "completed"


class Inquiry(SQLModel, table=True):
    """Contact / consultation inquiry form submission."""

    __tablename__: ClassVar[str] = "inquiries"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    name: str = Field(sa_column=Column(Text, nullable=False))
    email: str = Field(sa_column=Column(Text, nullable=False))
    phone: str = Field(sa_column=Column(Text, nullable=False))
    age: int = Field(nullable=False)
    preferred_date: Optional[str] = Field(default=None)
    plan: Optional[str] = Field(default=None)
    message: str = Field(default="", nullable=False)
    status: str = Field(default=InquiryStatus.PENDING.value, nullable=False)
    admin_note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
