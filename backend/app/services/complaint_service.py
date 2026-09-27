from redis import Redis
from sqlalchemy.orm import Session

from app.models import Complaint, Status
from app.repositories import complaint_repository as repo
from app.schemas import ComplaintCreate
from app.services.state_machine import validate_transition
from app.services.stats_service import invalidate_stats_cache
from app.services.triage_service import run_triage


def submit_complaint(db: Session, redis: Redis, data: ComplaintCreate) -> Complaint:
    result, triaged_by, latency_ms = run_triage(data.text, data.location, redis)

    complaint = repo.create_complaint(
        db,
        data,
        category=result.category,
        priority=result.priority,
        ai_summary=result.summary,
        triaged_by=triaged_by,
        triage_latency_ms=latency_ms,
    )

    invalidate_stats_cache(redis)  # new complaint must appear in stats immediately
    return complaint


def transition_status(db: Session, redis: Redis, complaint: Complaint, new_status: Status) -> Complaint:
    validate_transition(complaint.status, new_status)  # raises InvalidTransitionError -> 409
    updated = repo.update_status(db, complaint, new_status)
    invalidate_stats_cache(redis)
    return updated
