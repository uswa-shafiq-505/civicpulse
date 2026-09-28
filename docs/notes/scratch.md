# Day 3 acceptance results
1 pass - client-side validation, no network call
2 pass - valid submit -> category/priority/AI summary/llm:groq
3 pass - broken key -> rules:fallback (screenshot 3.5, providers 3.6)
4 pass - dashboard filters + pagination + page reset
5 pass - dashboard shows verbatim 409 message
6 pass (terminal) - 429 + Retry-After confirmed via burst loop
6 pending (UI) - UI 429 alert screenshot not captured; backend limiter confirmed working
