from fastapi import APIRouter, Depends, Response
from redis import Redis
from sqlalchemy.orm import Session

from app.db import get_db
from app.redis_client import get_redis
from app.schemas import StatsOut
from app.services.stats_service import get_stats

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def stats(response: Response, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    result, cache_hit = get_stats(db, redis)
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return result
