import json

import httpx

from app.config import settings
from app.models import Category, Priority
from app.providers.triage.base import NonRetryableTriageError, RetryableTriageError
from app.providers.triage.llm import _SYSTEM_PROMPT
from app.schemas import TriageResult


class OllamaTriage:
    """Fully offline path: local Ollama container, same interface as LLMTriage."""

    name = "llm:ollama"

    def __init__(self):
        self._client = httpx.Client(timeout=settings.TRIAGE_TIMEOUT_SECONDS)

    def triage(self, text: str, location: str) -> TriageResult:
        prompt = f"{_SYSTEM_PROMPT}\n<<<COMPLAINT>>>\nlocation: {location}\ntext: {text}\n<<<END>>>"
        try:
            resp = self._client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
            )
        except httpx.TimeoutException as e:
            raise RetryableTriageError(f"timeout: {e}") from e
        except httpx.RequestError as e:
            raise RetryableTriageError(f"network error: {e}") from e

        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            raise RetryableTriageError(f"upstream {resp.status_code}")
        if resp.status_code >= 400:
            raise NonRetryableTriageError(f"upstream {resp.status_code}: {resp.text[:200]}")

        try:
            body = resp.json()
            parsed = json.loads(body["response"])
            result = TriageResult(
                category=Category(parsed["category"]),
                priority=Priority(parsed["priority"]),
                summary=str(parsed["summary"])[:140],
                confidence=float(parsed["confidence"]),
            )
        except Exception as e:
            raise NonRetryableTriageError(f"malformed Ollama output: {e}") from e

        return result
