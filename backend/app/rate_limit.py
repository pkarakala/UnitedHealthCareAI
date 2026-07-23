from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default],
    storage_uri=settings.redis_url,
    # Fail-open: a Redis outage must degrade rate limiting, not take the API
    # down (also lets the test suite run without a Redis instance).
    swallow_errors=True,
    in_memory_fallback_enabled=True,
)
