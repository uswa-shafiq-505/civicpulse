from typing import Protocol

from app.schemas import TriageResult


class TriageProvider(Protocol):
    name: str

    def triage(self, text: str, location: str) -> TriageResult:
        ...


class RetryableTriageError(Exception):
    """Raised for timeout / 429 / 5xx style failures -> caller may retry once."""


class NonRetryableTriageError(Exception):
    """Raised for 400-style / malformed-output failures -> caller must not retry."""
