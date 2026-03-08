from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ArticleLocaleInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    excerpt: str = Field(default="", max_length=500)
    content: str = Field(default="")
    image_alt: str = Field(default="", alias="imageAlt", max_length=200)
    author: str = Field(default="", max_length=100)
    read_time: str = Field(default="", alias="readTime", max_length=20)
    tags: list[str] = Field(default_factory=list)
    model_config = {"populate_by_name": True}


class ArticleCreate(BaseModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9\-]+$")
    ja: ArticleLocaleInput
    ko: ArticleLocaleInput | None = None
    image_url: str | None = Field(default=None, alias="imageUrl")
    date: str | None = None
    model_config = {"populate_by_name": True}


class ArticleUpdate(BaseModel):
    ja: ArticleLocaleInput | None = None
    ko: ArticleLocaleInput | None = None
    image_url: str | None = Field(default=None, alias="imageUrl")
    date: str | None = None
    model_config = {"populate_by_name": True}


class ArticleResponse(BaseModel):
    id: str
    image_url: str | None
    image_url_raw: str | None = None
    date: str | None
    ja: dict[str, Any]
    ko: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ArticleCreateResponse(BaseModel):
    success: bool = True
    message: str
    article: ArticleResponse


class ArticleUpdateResponse(BaseModel):
    success: bool = True
    message: str
    article: ArticleResponse


class ArticleListResponse(BaseModel):
    success: bool = True
    articles: list[ArticleResponse]
    count: int
