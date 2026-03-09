# Validation & Sanitization

## Pydantic Input Validation

All external input MUST be validated via Pydantic schemas before processing.

### Field Constraints

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

class PostCreate(BaseModel):
    author: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    password: str = Field(min_length=4, max_length=50)
    experience: Optional[Literal["experienced", "inexperienced"]] = None
    category: Optional[Literal["question", "info", "chat"]] = None
```

### Enum Validation for Query Params

```python
from enum import Enum

class PostSortField(str, Enum):
    NEWEST = "newest"
    OLDEST = "oldest"
    LIKES = "likes"
    VIEWS = "views"
    COMMENTS = "comments"

class PostCategoryFilter(str, Enum):
    ALL = "all"
    QUESTION = "question"
    INFO = "info"
    CHAT = "chat"

class PostSearchType(str, Enum):
    ALL = "all"
    TITLE = "title"
    CONTENT = "content"
    AUTHOR = "author"

# In router — FastAPI validates enum automatically
sort: PostSortField = Query(default=PostSortField.NEWEST)
category: PostCategoryFilter = Query(default=PostCategoryFilter.ALL)
search_type: PostSearchType = Query(default=PostSearchType.ALL)
```

### Custom Validators

```python
from pydantic import field_validator

class InquiryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=254)
    phone: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=1, le=100)
    preferred_date: str | None = Field(default=None, max_length=50)
    plan: str | None = Field(default=None, max_length=100)
    message: str = Field(default="", max_length=5000)
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("有効なメールアドレスを入力してください")
        return v.strip().lower()
```

## XSS Sanitization

Applied server-side AFTER Pydantic validation, BEFORE storage.

```python
import re

XSS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", re.IGNORECASE),
    re.compile(r"on\w+\s*=\s*[\"'][^\"']*[\"']", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
    re.compile(r"<iframe\b[^>]*>", re.IGNORECASE),
    re.compile(r"<object\b[^>]*>", re.IGNORECASE),
    re.compile(r"<embed\b[^>]*>", re.IGNORECASE),
    re.compile(r"<form\b[^>]*>", re.IGNORECASE),
]

def sanitize_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    result: str = text.strip()
    for pattern in XSS_PATTERNS:
        result = pattern.sub("", result)
    return result
```

### Rules

1. **Always sanitize user-provided text** — author, title, content, messages
2. **Sanitize AFTER validation** — Pydantic validates length/format, then sanitize XSS
3. **Check for empty after sanitization** — Sanitization might strip all content

```python
from app.services.sanitize import sanitize_text
from app.services.exceptions import ValidationError

author = sanitize_text(body.author)
if not author:
    raise ValidationError("入力内容が無効です")
```

## Spam Detection

```python
from pydantic import BaseModel

class SpamCheckResult(BaseModel):
    is_spam: bool
    reason: str | None = None

SPAM_URL_THRESHOLD: int = 3

SPAM_KEYWORDS: re.Pattern[str] = re.compile(
    r"\b(casino|gambling|viagra|cialis|forex|crypto\s*trading|click\s*here|free\s*money|"
    r"buy\s*now|limited\s*offer|カジノ|ギャンブル|出会い系|副業|簡単に稼|即金|アダルト)\b",
    re.IGNORECASE,
)

def check_spam(content: str) -> SpamCheckResult:
    if not content:
        return SpamCheckResult(is_spam=False)

    # 1. URL flood check (>3 URLs)
    urls = re.findall(r"https?://\S+", content, re.IGNORECASE)
    if len(urls) > SPAM_URL_THRESHOLD:
        return SpamCheckResult(is_spam=True, reason=f"URLが多すぎます ({len(urls)}個検出)")

    # 2. Character repetition check (11+ repeated chars)
    if re.search(r"(.)\1{10,}", content):
        return SpamCheckResult(is_spam=True, reason="同じ文字の過度な繰り返しが検出されました")

    # 3. Keyword check (2+ spam keywords)
    if len(SPAM_KEYWORDS.findall(content)) >= 2:
        return SpamCheckResult(is_spam=True, reason="スパムの可能性があるコンテンツが検出されました")

    # 4. Line repetition check (5+ identical lines)
    lines = [line.strip().lower() for line in content.split("\n") if line.strip()]
    if len(lines) >= 5 and len(set(lines)) == 1:
        return SpamCheckResult(is_spam=True, reason="同じ内容の繰り返しが検出されました")

    return SpamCheckResult(is_spam=False)
```

## Validation Pipeline

```
Request → Pydantic Schema → Sanitize → Spam Check → Service Logic → Database
```

Each step must pass before proceeding to the next.

## Service Integration

```python
# In service layer (e.g., post_service.py)
from app.services.sanitize import sanitize_text
from app.services.spam import check_spam
from app.services.exceptions import ValidationError, SpamDetectedError

async def create(session: AsyncSession, body: PostCreate) -> PostCreateResponse:
    # 1. Sanitize
    author = sanitize_text(body.author)
    title = sanitize_text(body.title)
    content = sanitize_text(body.content)

    if not author or not title or not content:
        raise ValidationError("入力内容が無効です")

    # 2. Spam check
    spam_result = check_spam(f"{title} {content}")
    if spam_result.is_spam:
        raise SpamDetectedError(spam_result.reason or "スパムが検出されました")

    # 3. Continue with business logic...
```
