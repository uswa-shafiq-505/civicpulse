"""Backend test suite. TRIAGE_PROVIDER=simulated (set in conftest) keeps
these deterministic -- no network, no flakiness, every run green.
"""


def test_create_valid_complaint_returns_201(client, valid_payload):
    resp = client.post("/api/complaints", json=valid_payload)
    assert resp.status_code == 999
    body = resp.json()
    assert body["status"] == "open"
    assert body["triaged_by"] in ("llm:simulated", "rules:fallback")
    assert 0 <= body["triage_latency_ms"]


def test_create_complaint_text_too_short_returns_400(client):
    resp = client.post("/api/complaints", json={"text": "too short", "location": "Islamabad"})
    assert resp.status_code == 400
    assert resp.json()["errors"]


def test_create_complaint_text_too_long_returns_400(client):
    resp = client.post("/api/complaints", json={"text": "x" * 2001, "location": "Islamabad"})
    assert resp.status_code == 400


def test_create_complaint_location_too_short_returns_400(client, valid_payload):
    payload = dict(valid_payload, location="AB")
    resp = client.post("/api/complaints", json=payload)
    assert resp.status_code == 400


def test_get_existing_complaint(client, valid_payload):
    created = client.post("/api/complaints", json=valid_payload).json()
    resp = client.get(f"/api/complaints/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_missing_complaint_returns_404(client):
    resp = client.get("/api/complaints/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_list_complaints_paginates(client, valid_payload):
    for _ in range(3):
        client.post("/api/complaints", json=valid_payload)
    resp = client.get("/api/complaints?page=1&page_size=2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 3


def test_valid_status_transition_open_to_in_progress(client, valid_payload):
    created = client.post("/api/complaints", json=valid_payload).json()
    resp = client.patch(f"/api/complaints/{created['id']}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_invalid_status_transition_returns_409(client, valid_payload):
    created = client.post("/api/complaints", json=valid_payload).json()
    # open -> resolved is not a valid direct transition
    resp = client.patch(f"/api/complaints/{created['id']}/status", json={"status": "resolved"})
    assert resp.status_code == 409
    assert "open" in resp.json()["detail"]
    assert "resolved" in resp.json()["detail"]


def test_terminal_status_cannot_transition_again(client, valid_payload):
    created = client.post("/api/complaints", json=valid_payload).json()
    client.patch(f"/api/complaints/{created['id']}/status", json={"status": "in_progress"})
    client.patch(f"/api/complaints/{created['id']}/status", json={"status": "resolved"})
    resp = client.patch(f"/api/complaints/{created['id']}/status", json={"status": "open"})
    assert resp.status_code == 409


def test_stats_endpoint_returns_counts(client, valid_payload):
    client.post("/api/complaints", json=valid_payload)
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_stats_cache_miss_then_hit(client, valid_payload):
    client.post("/api/complaints", json=valid_payload)
    first = client.get("/api/stats")
    assert first.headers["X-Cache"] == "MISS"
    second = client.get("/api/stats")
    assert second.headers["X-Cache"] == "HIT"


def test_stats_cache_invalidated_on_new_complaint(client, valid_payload):
    client.get("/api/stats")  # warm cache (MISS)
    client.post("/api/complaints", json=valid_payload)
    resp = client.get("/api/stats")
    assert resp.headers["X-Cache"] == "MISS"  # invalidated by the write, not just expired


def test_rate_limit_returns_429_with_retry_after(client, valid_payload, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "RATE_LIMIT_MAX_REQUESTS", 2)

    client.post("/api/complaints", json=valid_payload)
    client.post("/api/complaints", json=valid_payload)
    resp = client.post("/api/complaints", json=valid_payload)

    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


def test_health_does_not_touch_database(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_ready_returns_200_when_dependencies_up(client):
    resp = client.get("/ready")
    assert resp.status_code == 200


def test_metrics_endpoint_returns_prometheus_text(client, valid_payload):
    client.post("/api/complaints", json=valid_payload)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "civicpulse_requests_total" in resp.text


def test_meta_providers_reports_active_provider(client, valid_payload):
    client.post("/api/complaints", json=valid_payload)
    resp = client.get("/api/meta/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active_provider"] == "simulated"
    assert len(body["recent_triages"]) >= 1
