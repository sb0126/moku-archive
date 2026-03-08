# Skill: Backend SQLModel Models & Pydantic Schemas

CRITICAL RULE: Every model, schema, function parameter, and return type MUST have explicit type annotations. `mypy --strict` compatibility is the baseline. No `Any` shortcuts except for JSONB dict fields.

## SQLModel Table Models

```python
# app/models/post.py
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Text, BigInteger
from sqlmodel import SQLModel, Field


class ExperienceType(str, Enum):
    EXPERIENCED = "experienced"
    INEXPERIENCED = "inexperienced"


class PostCategory(str, Enum):
    QUESTION = "question"
    INFO = "info"
    CHAT = "chat"


class Post(SQLModel, table=True):
    __tablename__ = "posts"

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
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class PostLike(SQLModel, table=True):
    __tablename__ = "post_likes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    post_id: str = Field(foreign_key="posts.id", nullable=False, index=True)
    visitor_id: str = Field(nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
```

```python
# app/models/comment.py
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    post_id: str = Field(foreign_key="posts.id", nullable=False, index=True)
    author: str = Field(sa_column=Column(Text, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    password: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
```

```python
# app/models/inquiry.py
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field


class InquiryStatus(str, Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    COMPLETED = "completed"


class Inquiry(SQLModel, table=True):
    __tablename__ = "inquiries"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    name: str = Field(sa_column=Column(Text, nullable=False))
    email: str = Field(sa_column=Column(Text, nullable=False))
    phone: str = Field(sa_column=Column(Text, nullable=False))
    age: int = Field(nullable=False)
    preferred_date: Optional[str] = Field(default=None)
    plan: Optional[str] = Field(default=None)
    message: str = Field(default="", nullable=False)
    status: str = Field(default=InquiryStatus.PENDING.value, nullable=False)
    admin_note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
```

```python
# app/models/article.py
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


class Article(SQLModel, table=True):
    __tablename__ = "articles"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    image_url: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    ja: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    ko: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
```

---

## Pydantic Request/Response Schemas

```python
# app/schemas/common.py
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    error: str
    details: str | None = None
```

```python
# app/schemas/post.py
from datetime import datetime
from enum import Enum
from typing import Optional, Literal

from pydantic import BaseModel, Field


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


class PostCreate(BaseModel):
    author: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)
    experience: Optional[Literal["experienced", "inexperienced"]] = None
    category: Optional[Literal["question", "info", "chat"]] = None


class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)


class PostResponse(BaseModel):
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


class PostListResponse(BaseModel):
    success: bool = True
    posts: list[PostResponse]
    count: int
    total: int
    total_pages: int
    current_page: int
    limit: int


class PostDeleteRequest(BaseModel):
    password: str | None = None
    is_admin: bool = False


class PasswordVerifyRequest(BaseModel):
    password: str = Field(min_length=1)


class PasswordVerifyResponse(BaseModel):
    success: bool = True
    verified: bool


class LikeToggleRequest(BaseModel):
    visitor_id: str = Field(alias="visitorId", min_length=8)
    model_config = {"populate_by_name": True}


class LikeResponse(BaseModel):
    success: bool = True
    liked: bool
    likes: int


class LikeStatusResponse(BaseModel):
    success: bool = True
    likes: int
    liked: bool


class BulkLikesRequest(BaseModel):
    post_ids: list[str] = Field(alias="postIds", max_length=100)
    model_config = {"populate_by_name": True}


class BulkLikesResponse(BaseModel):
    success: bool = True
    likes: dict[str, int]


class ViewIncrementResponse(BaseModel):
    success: bool = True
    views: int


class PinToggleResponse(BaseModel):
    success: bool = True
    message: str
    post: PostResponse
```

```python
# app/schemas/comment.py
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


class CommentDeleteRequest(BaseModel):
    password: str | None = None
    is_admin: bool = False
```

```python
# app/schemas/inquiry.py
import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class InquiryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    age: int = Field(ge=18, le=30)
    preferred_date: str = Field(alias="preferredDate")
    plan: str = Field(min_length=1, max_length=50)
    message: str = Field(default="", max_length=2000)
    model_config = {"populate_by_name": True}

    @field_validator("phone")
    @classmethod
    def validate_japanese_phone(cls, v: str) -> str:
        cleaned: str = re.sub(r"[\s\-()]", "", v)
        patterns: list[str] = [r"^0[6-9]0\d{8}$", r"^\+?81[6-9]0\d{8}$", r"^0\d{9,10}$"]
        if not any(re.match(p, cleaned) for p in patterns):
            raise ValueError("有効な電話番号を入力してください")
        return v


class InquiryResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    age: int
    preferred_date: str | None
    plan: str | None
    message: str
    status: str
    admin_note: str | None
    created_at: datetime
    updated_at: datetime


class InquiryListResponse(BaseModel):
    success: bool = True
    inquiries: list[InquiryResponse]
    count: int


class InquiryStatusUpdate(BaseModel):
    status: Literal["pending", "contacted", "completed"]
    admin_note: str | None = None
```

```python
# app/schemas/article.py
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


class ArticleListResponse(BaseModel):
    success: bool = True
    articles: list[ArticleResponse]
    count: int
```

```python
# app/schemas/admin.py
from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    password: str = Field(min_length=1)


class AdminLoginResponse(BaseModel):
    success: bool = True
    authenticated: bool = True
    token: str


class AdminStats(BaseModel):
    total_inquiries: int
    pending_inquiries: int
    contacted_inquiries: int
    completed_inquiries: int
    total_posts: int
    total_views: int
    total_comments: int


class AdminStatsResponse(BaseModel):
    success: bool = True
    stats: AdminStats
```

```python
# app/schemas/config.py
from pydantic import BaseModel, Field


class VerificationConfig(BaseModel):
    google: str | None = None
    naver: str | None = None


class SiteConfigResponse(BaseModel):
    ga_measurement_id: str = Field(serialization_alias="gaMeasurementId")
    verification: VerificationConfig
```
