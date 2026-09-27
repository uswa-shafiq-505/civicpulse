"""Seed script must be idempotent: running it twice leaves the same row count."""
from scripts.seed import _COMPLAINTS, run
from app.models import Complaint


def test_seed_has_at_least_30_complaints():
    assert len(_COMPLAINTS) >= 30


def test_seed_is_idempotent(db_session, monkeypatch):
    from scripts import seed as seed_module
    monkeypatch.setattr(seed_module, "SessionLocal", lambda: db_session)

    seed_module.run()
    count_after_first = db_session.query(Complaint).count()

    seed_module.run()
    count_after_second = db_session.query(Complaint).count()

    assert count_after_first == len(_COMPLAINTS)
    assert count_after_second == count_after_first
