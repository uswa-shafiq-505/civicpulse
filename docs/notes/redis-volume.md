# Why Redis has a volume (§2.4)

Redis does two jobs in CivicPulse. The stats cache could be rebuilt from Postgres freely — losing it costs one extra database query. But the rate-limit counters and the 24 h LLM triage cache hold real cost: the limiter is the only thing standing between one bored user and our entire daily Groq quota, and the triage cache saves inference for duplicate complaints (a burst main gets reported by nine neighbours).

If Redis restarted empty, a caller could reset their own rate limit and re-spend inference quota. Persisting AOF is therefore cheap insurance against a class of abuse and cost, not a way to preserve reproducible state.