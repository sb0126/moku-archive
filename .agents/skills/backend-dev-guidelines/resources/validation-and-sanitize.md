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

# In router — FastAPI validates enum automatically
sort: PostSortField = Query(default=PostSortField.NEWEST)
```

### Custom Validators

```python
from pydantic import field_validator

class InquiryCreate(BaseModel):
    email: str = Field(max_length=254)
    phone: str | None = Field(default=None, max_length=20)
    
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
author = sanitize_text(body.author)
if not author:
    raise PostValidationError("入力内容が無効です")
```

## Spam Detection

```python
from pydantic import BaseModel

class SpamCheckResult(BaseModel):
    is_spam: bool
    reason: str | None = None

def check_spam(content: str) -> SpamCheckResult:
    if not content:
        return SpamCheckResult(is_spam=False)

    # URL flood check
    urls = re.findall(r"https?://\S+", content, re.IGNORECASE)
    if len(urls) > 3:
        return SpamCheckResult(is_spam=True, reason="URLが多すぎます")

    # Character repetition check
    if re.search(r"(.)\1{10,}", content):
        return SpamCheckResult(is_spam=True, reason="同じ文字の繰り返し")

    # Keyword check
    if len(SPAM_KEYWORDS.findall(content)) >= 2:
        return SpamCheckResult(is_spam=True, reason="スパムコンテンツ検出")

    return SpamCheckResult(is_spam=False)
```

## Validation Pipeline

```
Request → Pydantic Schema → Sanitize → Spam Check → Service Logic → Database
```

Each step must pass before proceeding to the next.
