from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    author: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=5000)
    password: str = Field(min_length=4, max_length=50)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    password: str = Field(min_length=4, max_length=50)


class CommentResponse(BaseModel):
    id: str
    post_id: str
    author: str
    content: str
    created_at: datetime
    updated_at: datetime


class CommentListResponse(BaseModel):
    success: bool = True
    comments: list[CommentResponse]
    count: int


class CommentCreateResponse(BaseModel):
    success: bool = True
    message: str
    comment: CommentResponse
    commentCount: int


class CommentUpdateResponse(BaseModel):
    success: bool = True
    message: str
    comment: CommentResponse


class CommentDeleteRequest(BaseModel):
    password: str | None = None
