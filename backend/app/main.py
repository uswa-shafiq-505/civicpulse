import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.routes import complaints, health, meta, stats

# --- structured JSON logging to stdout ---


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        return json.dumps(payload)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])

# --- simple in-process metrics (Prometheus text format) ---
_request_count = 0
_request_latencies_ms: list[float] = []
_triage_fallback_count = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Graceful shutdown: uvicorn handles SIGTERM by stopping new connections
    # and draining in-flight requests before this point is reached; nothing
    # additional to release here since DB/Redis use short-lived connections
    # from a pool that closes cleanly on process exit.
    logging.getLogger("civicpulse").info("shutting down gracefully")


app = FastAPI(title="CivicPulse", lifespan=lifespan)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global _request_count
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.monotonic()

        response = await call_next(request)

        latency_ms = (time.monotonic() - start) * 1000
        _request_count += 1
        _request_latencies_ms.append(latency_ms)

        response.headers["X-Request-ID"] = request_id
        logging.getLogger("civicpulse.request").info(
            "%s %s %d %.1fms", request.method, request.url.path, response.status_code, latency_ms,
            extra={"request_id": request_id},
        )
        return response


app.add_middleware(RequestIDMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": "validation error", "errors": errors})


app.include_router(health.router)
app.include_router(complaints.router)
app.include_router(stats.router)
app.include_router(meta.router)


@app.get("/metrics")
def metrics():
    avg_latency = (
        sum(_request_latencies_ms) / len(_request_latencies_ms) if _request_latencies_ms else 0
    )
    lines = [
        "# HELP civicpulse_requests_total Total HTTP requests handled",
        "# TYPE civicpulse_requests_total counter",
        f"civicpulse_requests_total {_request_count}",
        "# HELP civicpulse_request_latency_ms_avg Average request latency in ms",
        "# TYPE civicpulse_request_latency_ms_avg gauge",
        f"civicpulse_request_latency_ms_avg {avg_latency:.2f}",
        "# HELP civicpulse_triage_fallback_total Times triage fell back to rules",
        "# TYPE civicpulse_triage_fallback_total counter",
        f"civicpulse_triage_fallback_total {_triage_fallback_count}",
    ]
    return PlainTextResponse("\n".join(lines) + "\n")
