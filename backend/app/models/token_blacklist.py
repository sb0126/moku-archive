"""TokenBlacklist model — stores revoked JWT identifiers in PostgreSQL.

Replaces the previous Redis-based JWT blacklist. Expired entries should be
cleaned up periodically via ``cleanup_expired_tokens()``.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel


class TokenBlacklist(SQLModel, table=True):
    """A revoked JWT, identified by its ``jti`` claim."""

    __tablename__ = "token_blacklist"

    jti: str = Field(
        sa_column=Column(String(64), primary_key=True),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
