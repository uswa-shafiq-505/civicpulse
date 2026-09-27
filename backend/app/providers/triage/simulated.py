import hashlib

from app.models import Category, Priority
from app.providers.triage.base import NonRetryableTriageError, RetryableTriageError
from app.schemas import TriageResult


class SimulatedTriage:
    """Deterministic fake for CI. No network. Seeded by content hash.

    Configurable failure injection via the `fail_mode` constructor arg, used
    by tests to exercise timeout/retry/fallback and malformed-output paths
    without any flakiness.
    """

    name = "llm:simulated"

    def __init__(self, fail_mode: str | None = None):
        # fail_mode: None | "always_raise" | "malformed"
        self.fail_mode = fail_mode

    def triage(self, text: str, location: str) -> TriageResult:
        if self.fail_mode == "always_raise":
            raise RetryableTriageError("simulated provider configured to fail")
        if self.fail_mode == "malformed":
            raise NonRetryableTriageError("simulated provider returned malformed output")

        digest = hashlib.sha256((text + location).encode()).hexdigest()
        seed = int(digest[:8], 16)

        categories = list(Category)
        priorities = list(Priority)
        category = categories[seed % len(categories)]
        priority = priorities[seed % len(priorities)]

        summary = text.strip().replace("\n", " ")[:137]
        if len(text.strip()) > 137:
            summary += "..."

        confidence = 0.6 + (seed % 40) / 100.0  # 0.60 - 0.99, deterministic
        return TriageResult(
            category=category, priority=priority, summary=summary, confidence=round(confidence, 2)
        )
