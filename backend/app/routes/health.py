from fastapi import APIRouter, Depends, Response
from redis import Redis, RedisError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    # Liveness: process is alive. Must NOT touch the database.
    return {"status": "alive"}


@router.get("/ready")
def ready(response: Response, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    # Readiness: 200 only if Postgres AND Redis are both reachable.
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001 -- readiness must catch ANY DB failure, not just known ones
        response.status_code = 503
        return {"status": "not ready", "failed_dependency": "postgres", "error": str(e)}

    try:
        redis.ping()
    except RedisError as e:
        response.status_code = 503
        return {"status": "not ready", "failed_dependency": "redis", "error": str(e)}

    return {"status": "ready"}
