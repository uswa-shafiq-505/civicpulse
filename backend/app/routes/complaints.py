from fastapi import APIRouter, Depends, HTTPException, Query, Request
from redis import Redis
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, Priority, Status
from app.redis_client import get_redis
from app.repositories import complaint_repository as repo
from app.schemas import ComplaintCreate, ComplaintListOut, ComplaintOut, StatusUpdate
from app.services import complaint_service
from app.services.rate_limiter import RateLimitExceeded, check_rate_limit
from app.services.state_machine import InvalidTransitionError

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintOut, status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    request: Request,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    client_ip = request.client.host if request.client else "unknown"
    try:
        check_rate_limit(redis, client_ip)
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded",
            headers={"Retry-After": str(e.retry_after)},
        ) from e

    complaint = complaint_service.submit_complaint(db, redis, payload)
    return complaint


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = repo.get_complaint(db, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="complaint not found")
    return complaint


@router.get("", response_model=ComplaintListOut)
def list_complaints(
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = repo.list_complaints(db, category, priority, status, page, page_size)
    return ComplaintListOut(
        items=[ComplaintOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(
    complaint_id: str,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    complaint = repo.get_complaint(db, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="complaint not found")

    try:
        updated = complaint_service.transition_status(db, redis, complaint, payload.status)
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=409,
            detail=f"invalid transition from '{e.current.value}' to '{e.attempted.value}'",
        ) from e

    return updated
