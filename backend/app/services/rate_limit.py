from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    # In-memory storage (default) — sufficient for our scale.
    # Counters reset on server restart, which is acceptable.
)
