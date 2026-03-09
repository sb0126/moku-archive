"""Re-export all table models for convenient imports."""

from app.models.article import Article
from app.models.comment import Comment
from app.models.inquiry import Inquiry, InquiryStatus
from app.models.post import (
    ExperienceType,
    Post,
    PostCategory,
    PostLike,
)
from app.models.token_blacklist import TokenBlacklist

__all__: list[str] = [
    "Article",
    "Comment",
    "ExperienceType",
    "Inquiry",
    "InquiryStatus",
    "Post",
    "PostCategory",
    "PostLike",
    "TokenBlacklist",
]
