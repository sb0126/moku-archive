"""Article table model."""

from datetime import datetime, timezone
from typing import Any, ClassVar, Optional

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now — replaces deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Article(SQLModel, table=True):
    """SEO article with per-locale JSONB content (ja / ko)."""

    __tablename__: ClassVar[str] = "articles"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    image_url: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    ja: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    ko: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
