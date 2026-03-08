import re

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

    urls: list[str] = re.findall(r"https?://\S+", content, re.IGNORECASE)
    if len(urls) > SPAM_URL_THRESHOLD:
        return SpamCheckResult(is_spam=True, reason=f"URLが多すぎます ({len(urls)}個検出)")

    if re.search(r"(.)\1{10,}", content):
        return SpamCheckResult(is_spam=True, reason="同じ文字の過度な繰り返しが検出されました")

    keyword_matches: list[str] = SPAM_KEYWORDS.findall(content)
    if len(keyword_matches) >= 2:
        return SpamCheckResult(is_spam=True, reason="スパムの可能性があるコンテンツが検出されました")

    lines: list[str] = [line.strip().lower() for line in content.split("\n") if line.strip()]
    if len(lines) >= 5 and len(set(lines)) == 1:
        return SpamCheckResult(is_spam=True, reason="同じ内容の繰り返しが検出されました")

    return SpamCheckResult(is_spam=False)
