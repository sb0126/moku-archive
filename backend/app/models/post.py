"""Post and PostLike table models."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, Optional

from sqlalchemy import Column, Text, BigInteger
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now — replaces deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


class ExperienceType(str, Enum):
    """Allowed values for Post.experience."""

    EXPERIENCED = "experienced"
    INEXPERIENCED = "inexperienced"


class PostCategory(str, Enum):
    """Allowed values for Post.category."""

    QUESTION = "question"
    INFO = "info"
    CHAT = "chat"


class Post(SQLModel, table=True):
    """Community board post."""

    __tablename__: ClassVar[str] = "posts"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    numeric_id: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    title: str = Field(sa_column=Column(Text, nullable=False))
    author: str = Field(sa_column=Column(Text, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    password: str = Field(sa_column=Column(Text, nullable=False))
    views: int = Field(default=0, nullable=False)
    comment_count: int = Field(default=0, nullable=False)
    pinned: bool = Field(default=False, nullable=False)
    pinned_at: Optional[datetime] = Field(default=None)
    experience: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)


class PostLike(SQLModel, table=True):
    """One visitor ↔ one post like (normalized counting)."""

    __tablename__: ClassVar[str] = "post_likes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    post_id: str = Field(foreign_key="posts.id", nullable=False, index=True)
    visitor_id: str = Field(nullable=False, index=True)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
