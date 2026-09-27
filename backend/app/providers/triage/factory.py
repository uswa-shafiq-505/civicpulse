from app.config import settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def get_primary_provider() -> TriageProvider:
    """Selects the primary provider via TRIAGE_PROVIDER env var.

    Import of llm/ollama modules is deferred so that `simulated`/`rules`
    (used in CI and tests) never require httpx network setup or API keys.
    """
    provider = settings.TRIAGE_PROVIDER.lower()

    if provider == "simulated":
        return SimulatedTriage()
    if provider == "rules":
        return RuleBasedTriage()
    if provider == "llm":
        from app.providers.triage.llm import LLMTriage
        return LLMTriage()
    if provider == "ollama":
        from app.providers.triage.ollama import OllamaTriage
        return OllamaTriage()

    raise ValueError(f"Unknown TRIAGE_PROVIDER: {settings.TRIAGE_PROVIDER}")


def get_fallback_provider() -> TriageProvider:
    return RuleBasedTriage()
