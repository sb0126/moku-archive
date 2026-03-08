"""Domain exceptions — framework-agnostic, translatable to HTTP errors in routers."""


class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "リソースが見つかりません") -> None:
        super().__init__(message, status_code=404)


class ForbiddenError(DomainError):
    """Raised when authentication succeeds but authorization fails."""

    def __init__(self, message: str = "パスワードが正しくありません") -> None:
        super().__init__(message, status_code=403)


class ConflictError(DomainError):
    """Raised when a unique-constraint would be violated."""

    def __init__(self, message: str = "リソースが既に存在します") -> None:
        super().__init__(message, status_code=409)


class ValidationError(DomainError):
    """Raised when input validation (beyond Pydantic) fails."""

    def __init__(self, message: str = "入力内容が無効です") -> None:
        super().__init__(message, status_code=400)


class SpamDetectedError(DomainError):
    """Raised when spam content is detected."""

    def __init__(self, message: str = "スパムが検出されました") -> None:
        super().__init__(message, status_code=400)
