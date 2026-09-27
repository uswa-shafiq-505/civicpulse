import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://civicpulse:civicpulse@postgres:5432/civicpulse",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    TRIAGE_PROVIDER: str = os.getenv("TRIAGE_PROVIDER", "simulated")  # simulated|rules|llm|ollama
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

    TRIAGE_TIMEOUT_SECONDS: float = float(os.getenv("TRIAGE_TIMEOUT_SECONDS", "10"))
    TRIAGE_CACHE_TTL_SECONDS: int = int(os.getenv("TRIAGE_CACHE_TTL_SECONDS", str(24 * 3600)))

    STATS_CACHE_TTL_SECONDS: int = int(os.getenv("STATS_CACHE_TTL_SECONDS", "30"))

    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "20"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


settings = Settings()
