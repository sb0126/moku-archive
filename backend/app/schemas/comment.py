from datetime import datetime

from pydantic import Field

from app.schemas.common import CamelModel


class CommentCreate(CamelModel):
    author: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=5000)
    password: str = Field(min_length=4, max_length=50)


class CommentUpdate(CamelModel):
    content: str = Field(min_length=1, max_length=5000)
    password: str = Field(min_length=4, max_length=50)


class CommentResponse(CamelModel):
    id: str
    post_id: str
    author: str
    content: str
    created_at: datetime
    updated_at: datetime


class CommentListResponse(CamelModel):
    success: bool = True
    comments: list[CommentResponse]
    count: int


class CommentCreateResponse(CamelModel):
    success: bool = True
    message: str
    comment: CommentResponse
    comment_count: int


class CommentUpdateResponse(CamelModel):
    success: bool = True
    message: str
    comment: CommentResponse


class CommentDeleteRequest(CamelModel):
    password: str | None = None

