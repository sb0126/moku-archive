from datetime import datetime
from enum import Enum
from typing import Optional, Literal

from pydantic import Field

from app.schemas.common import CamelModel


class PostSortField(str, Enum):
    NEWEST = "newest"
    OLDEST = "oldest"
    LIKES = "likes"
    VIEWS = "views"
    COMMENTS = "comments"


class PostSearchType(str, Enum):
    TITLE = "title"
    AUTHOR = "author"
    CONTENT = "content"


class PostCategoryFilter(str, Enum):
    QUESTION = "question"
    INFO = "info"
    CHAT = "chat"


class PostCreate(CamelModel):
    author: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)
    experience: Optional[Literal["experienced", "inexperienced"]] = None
    category: Optional[Literal["question", "info", "chat"]] = None


class PostUpdate(CamelModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)


class PostResponse(CamelModel):
    id: str
    numeric_id: int
    title: str
    author: str
    content: str
    views: int
    comments: int
    pinned: bool
    pinned_at: datetime | None
    experience: str | None
    category: str | None
    created_at: datetime
    updated_at: datetime


class PostListResponse(CamelModel):
    success: bool = True
    posts: list[PostResponse]
    count: int
    total: int
    total_pages: int
    current_page: int
    limit: int


class PostCreateResponse(CamelModel):
    success: bool = True
    message: str
    post: PostResponse


class PostUpdateResponse(CamelModel):
    success: bool = True
    message: str
    post: PostResponse


class PostDeleteRequest(CamelModel):
    password: str | None = None


class PasswordVerifyRequest(CamelModel):
    password: str = Field(min_length=1)


class PasswordVerifyResponse(CamelModel):
    success: bool = True
    verified: bool


class LikeToggleRequest(CamelModel):
    visitor_id: str = Field(alias="visitorId", min_length=8)


class LikeResponse(CamelModel):
    success: bool = True
    liked: bool
    likes: int


class LikeStatusResponse(CamelModel):
    success: bool = True
    likes: int
    liked: bool


class BulkLikesRequest(CamelModel):
    post_ids: list[str] = Field(alias="postIds", max_length=100)


class BulkLikesResponse(CamelModel):
    success: bool = True
    likes: dict[str, int]


class ViewIncrementResponse(CamelModel):
    success: bool = True
    views: int


class PinToggleResponse(CamelModel):
    success: bool = True
    message: str
    post: PostResponse

