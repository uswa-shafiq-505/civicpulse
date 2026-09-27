from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, Complaint, Priority, Status
from app.schemas import ComplaintCreate, StatsOut

# All SQL lives here, and nowhere else (routes/services never touch the DB session directly).


def create_complaint(
    db: Session,
    data: ComplaintCreate,
    category: Category,
    priority: Priority,
    ai_summary: str,
    triaged_by: str,
    triage_latency_ms: int,
) -> Complaint:
    complaint = Complaint(
        text=data.text,
        location=data.location,
        reporter_contact=data.reporter_contact,
        category=category,
        priority=priority,
        status=Status.open,
        ai_summary=ai_summary,
        triaged_by=triaged_by,
        triage_latency_ms=triage_latency_ms,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def get_complaint(db: Session, complaint_id: str) -> Complaint | None:
    return db.get(Complaint, complaint_id)


def list_complaints(
    db: Session,
    category: Category | None,
    priority: Priority | None,
    status: Status | None,
    page: int,
    page_size: int,
) -> tuple[list[Complaint], int]:
    query = select(Complaint)
    count_query = select(func.count()).select_from(Complaint)

    if category is not None:
        query = query.where(Complaint.category == category)
        count_query = count_query.where(Complaint.category == category)
    if priority is not None:
        query = query.where(Complaint.priority == priority)
        count_query = count_query.where(Complaint.priority == priority)
    if status is not None:
        query = query.where(Complaint.status == status)
        count_query = count_query.where(Complaint.status == status)

    total = db.execute(count_query).scalar_one()
    query = query.order_by(Complaint.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().all()

    return list(items), total


def update_status(db: Session, complaint: Complaint, new_status: Status) -> Complaint:
    complaint.status = new_status
    db.commit()
    db.refresh(complaint)
    return complaint


def get_stats_from_db(db: Session) -> StatsOut:
    total = db.execute(select(func.count()).select_from(Complaint)).scalar_one()

    by_category_rows = db.execute(
        select(Complaint.category, func.count()).group_by(Complaint.category)
    ).all()
    by_priority_rows = db.execute(
        select(Complaint.priority, func.count()).group_by(Complaint.priority)
    ).all()

    return StatsOut(
        total=total,
        by_category={c.value: n for c, n in by_category_rows},
        by_priority={p.value: n for p, n in by_priority_rows},
    )
