"""initial_schema

Revision ID: 7211687d757b
Revises:
Create Date: 2026-03-09 16:22:05.011884

Creates all existing tables that were previously managed via
SQLModel.metadata.create_all().  This baseline migration allows Alembic
to track all future schema changes incrementally.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7211687d757b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables matching the current SQLModel definitions."""

    # ── posts ─────────────────────────────────────────────────
    op.create_table(
        "posts",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("numeric_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("password", sa.Text(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pinned_at", sa.DateTime(), nullable=True),
        sa.Column("experience", sa.VARCHAR(), nullable=True),
        sa.Column("category", sa.VARCHAR(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # ── post_likes ────────────────────────────────────────────
    op.create_table(
        "post_likes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("post_id", sa.Text(), sa.ForeignKey("posts.id"), nullable=False, index=True),
        sa.Column("visitor_id", sa.VARCHAR(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── comments ──────────────────────────────────────────────
    op.create_table(
        "comments",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("post_id", sa.Text(), sa.ForeignKey("posts.id"), nullable=False, index=True),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("password", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # ── articles ──────────────────────────────────────────────
    op.create_table(
        "articles",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("image_url", sa.VARCHAR(), nullable=True),
        sa.Column("date", sa.VARCHAR(), nullable=True),
        sa.Column("ja", postgresql.JSONB(), nullable=False),
        sa.Column("ko", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # ── inquiries ─────────────────────────────────────────────
    op.create_table(
        "inquiries",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("preferred_date", sa.VARCHAR(), nullable=True),
        sa.Column("plan", sa.VARCHAR(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.VARCHAR(), nullable=False, server_default="pending"),
        sa.Column("admin_note", sa.VARCHAR(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("inquiries")
    op.drop_table("articles")
    op.drop_table("comments")
    op.drop_table("post_likes")
    op.drop_table("posts")
