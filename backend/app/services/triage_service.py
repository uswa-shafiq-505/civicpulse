import hashlib
import json
import logging
import time

from redis import Redis

from app.config import settings
from app.providers.triage.base import NonRetryableTriageError, RetryableTriageError, TriageProvider
from app.providers.triage.factory import get_fallback_provider, get_primary_provider
from app.schemas import TriageResult

logger = logging.getLogger("civicpulse.triage")

_recent_triages: list[dict] = []  # ring buffer for GET /api/meta/providers
_RECENT_LIMIT = 20

_cache_hits = 0
_cache_misses = 0


def _content_hash(text: str, location: str) -> str:
    return hashlib.sha256((text.strip() + "|" + location.strip()).encode()).hexdigest()


def _record(provider_name: str, latency_ms: int, fallback: bool) -> None:
    _recent_triages.insert(0, {
        "provider": provider_name,
        "latency_ms": latency_ms,
        "fallback": fallback,
    })
    del _recent_triages[_RECENT_LIMIT:]


def get_recent_triages() -> list[dict]:
    return list(_recent_triages)


def get_cache_hit_rate() -> float:
    total = _cache_hits + _cache_misses
    return round(_cache_hits / total, 4) if total else 0.0


def run_triage(
    text: str,
    location: str,
    redis: Redis,
    provider: TriageProvider | None = None,
) -> tuple[TriageResult, str, int]:
    """Runs the full triage pipeline: cache -> primary (with 1 jittered retry
    on retryable errors) -> rules fallback. Returns (result, triaged_by, latency_ms).
    """
    global _cache_hits, _cache_misses

    cache_key = f"triage:{_content_hash(text, location)}"
    cached = redis.get(cache_key)
    if cached:
        _cache_hits += 1
        data = json.loads(cached)
        result = TriageResult(**data["result"])
        return result, data["triaged_by"], 0
    _cache_misses += 1

    primary = provider or get_primary_provider()
    start = time.monotonic()
    triaged_by = primary.name
    fallback_used = False

    try:
        result = primary.triage(text, location)
    except RetryableTriageError as e:
        logger.warning("triage retryable error, retrying once: provider=%s error=%s", primary.name, e)
        try:
            result = primary.triage(text, location)
        except (RetryableTriageError, NonRetryableTriageError) as e2:
            logger.warning(
                "triage failed after retry, falling back to rules: provider=%s error_class=%s",
                primary.name, type(e2).__name__,
            )
            result = get_fallback_provider().triage(text, location)
            triaged_by = "rules:fallback"
            fallback_used = True
    except NonRetryableTriageError as e:
        logger.warning(
            "triage non-retryable error, falling back to rules: provider=%s error_class=%s",
            primary.name, type(e).__name__,
        )
        result = get_fallback_provider().triage(text, location)
        triaged_by = "rules:fallback"
        fallback_used = True

    latency_ms = int((time.monotonic() - start) * 1000)
    _record(triaged_by, latency_ms, fallback_used)

    redis.set(
        cache_key,
        json.dumps({"result": result.model_dump(), "triaged_by": triaged_by}),
        ex=settings.TRIAGE_CACHE_TTL_SECONDS,
    )

    return result, triaged_by, latency_ms
