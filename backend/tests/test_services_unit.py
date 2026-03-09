"""Unit tests for pure service functions (no DB, no HTTP).

Covers: sanitize_text, check_spam, auth helpers.
"""

from app.services.auth import (
    create_admin_token,
    hash_password,
    needs_rehash,
    verify_admin_token,
    verify_password,
)
from app.services.sanitize import sanitize_text
from app.services.spam import check_spam


# ═══════════════════════════════════════════════════════════════
# sanitize_text
# ═══════════════════════════════════════════════════════════════


def test_sanitize_removes_script_tags():
    result = sanitize_text('<script>alert("xss")</script>Hello')
    assert "<script>" not in result.lower()
    assert "Hello" in result


def test_sanitize_removes_onload():
    result = sanitize_text('<img onload="alert(1)" src="x">')
    assert "onload" not in result.lower()


def test_sanitize_removes_javascript_protocol():
    result = sanitize_text('<a href="javascript:void(0)">click</a>')
    assert "javascript:" not in result.lower()


def test_sanitize_removes_iframe():
    result = sanitize_text('<iframe src="http://evil.com"></iframe>content')
    assert "<iframe" not in result.lower()
    assert "content" in result


def test_sanitize_removes_form():
    result = sanitize_text('<form action="/steal">fields</form>')
    assert "<form" not in result.lower()


def test_sanitize_preserves_normal_text():
    text = "これは普通のテキストです。Hello World!"
    assert sanitize_text(text) == text


def test_sanitize_preserves_html_entities():
    result = sanitize_text("Coffee &amp; Tea")
    assert result == "Coffee &amp; Tea"


def test_sanitize_strips_whitespace():
    assert sanitize_text("  hello  ") == "hello"


def test_sanitize_empty_input():
    assert sanitize_text("") == ""


def test_sanitize_none_like():
    # The function checks isinstance, so passing a non-string should return ""
    assert sanitize_text("") == ""


# ═══════════════════════════════════════════════════════════════
# check_spam
# ═══════════════════════════════════════════════════════════════


def test_spam_clean_content():
    result = check_spam("日本のビザ取得について教えてください")
    assert result.is_spam is False


def test_spam_empty_content():
    result = check_spam("")
    assert result.is_spam is False


def test_spam_too_many_urls():
    result = check_spam(
        "http://a.com http://b.com http://c.com http://d.com"
    )
    assert result.is_spam is True
    assert "URL" in (result.reason or "")


def test_spam_repeated_characters():
    result = check_spam("aaaaaaaaaaaaaaaa")  # more than 10 repeated
    assert result.is_spam is True


def test_spam_keywords():
    result = check_spam("Free casino gambling opportunity!")
    assert result.is_spam is True


def test_spam_japanese_keywords():
    result = check_spam("カジノ ギャンブル で稼ごう")
    assert result.is_spam is True


def test_spam_repeated_lines():
    content = "\n".join(["spam line"] * 5)
    result = check_spam(content)
    assert result.is_spam is True


def test_spam_single_keyword_not_flagged():
    """A single keyword alone shouldn't trigger spam (threshold is 2)."""
    result = check_spam("I went to the casino once.")
    assert result.is_spam is False


def test_spam_under_url_threshold():
    """Three URLs is at the threshold, not over."""
    result = check_spam("http://a.com http://b.com http://c.com")
    assert result.is_spam is False


# ═══════════════════════════════════════════════════════════════
# auth — password hashing
# ═══════════════════════════════════════════════════════════════


def test_hash_and_verify_password():
    hashed = hash_password("mysecretpass")
    assert hashed.startswith("$2b$")
    assert verify_password("mysecretpass", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_verify_plaintext_password():
    """Legacy plaintext passwords should still verify."""
    assert verify_password("legacy123", "legacy123") is True
    assert verify_password("wrong", "legacy123") is False


def test_verify_sha256_salted_password():
    """Legacy SHA-256 salted passwords (salt:hash format)."""
    import hashlib

    salt = "abcdef01"
    password = "oldpass"
    expected_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    stored = f"{salt}:{expected_hash}"

    assert verify_password("oldpass", stored) is True
    assert verify_password("wrong", stored) is False


def test_needs_rehash():
    bcrypt_hash = hash_password("test")
    assert needs_rehash(bcrypt_hash) is False
    assert needs_rehash("plaintext") is True
    assert needs_rehash("salt:hash") is True


# ═══════════════════════════════════════════════════════════════
# auth — JWT
# ═══════════════════════════════════════════════════════════════


def test_create_and_verify_admin_token():
    token = create_admin_token()
    assert isinstance(token, str)
    assert verify_admin_token(token) is True


def test_verify_invalid_token():
    assert verify_admin_token("invalid.token.here") is False
    assert verify_admin_token("") is False


def test_verify_non_admin_token():
    """A valid JWT without 'admin' role should fail."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.config import settings

    payload = {
        "role": "user",  # not admin
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    assert verify_admin_token(token) is False
