"""Comment table model."""

from datetime import datetime, timezone
from typing import ClassVar

from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now — replaces deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Comment(SQLModel, table=True):
    """Comment on a community post (CASCADE-deleted with parent)."""

    __tablename__: ClassVar[str] = "comments"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    post_id: str = Field(foreign_key="posts.id", nullable=False, index=True)
    author: str = Field(sa_column=Column(Text, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    password: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)
