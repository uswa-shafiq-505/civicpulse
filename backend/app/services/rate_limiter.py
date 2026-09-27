import time

from redis import Redis

from app.config import settings


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"rate limit exceeded, retry after {retry_after}s")


def check_rate_limit(redis: Redis, client_ip: str) -> None:
    """Fixed-window counter in Redis, keyed by client IP. Distributed so it
    works correctly across multiple backend pods behind the HPA."""
    window = int(time.time() // settings.RATE_LIMIT_WINDOW_SECONDS)
    key = f"ratelimit:{client_ip}:{window}"

    count = redis.incr(key)
    if count == 1:
        redis.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)

    if count > settings.RATE_LIMIT_MAX_REQUESTS:
        ttl = redis.ttl(key)
        raise RateLimitExceeded(retry_after=max(ttl, 1))
