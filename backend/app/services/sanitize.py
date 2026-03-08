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
