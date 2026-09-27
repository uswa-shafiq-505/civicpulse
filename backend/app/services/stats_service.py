import json

from redis import Redis
from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.complaint_repository import get_stats_from_db
from app.schemas import StatsOut

_STATS_CACHE_KEY = "stats:aggregate"


def get_stats(db: Session, redis: Redis) -> tuple[StatsOut, bool]:
    """Returns (stats, cache_hit)."""
    cached = redis.get(_STATS_CACHE_KEY)
    if cached:
        return StatsOut(**json.loads(cached)), True

    stats = get_stats_from_db(db)
    redis.set(_STATS_CACHE_KEY, stats.model_dump_json(), ex=settings.STATS_CACHE_TTL_SECONDS)
    return stats, False


def invalidate_stats_cache(redis: Redis) -> None:
    redis.delete(_STATS_CACHE_KEY)
