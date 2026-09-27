import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Category(str, enum.Enum):  # noqa: UP042 -- kept for SQLAlchemy Enum() compatibility
    water = "water"
    electricity = "electricity"
    sanitation = "sanitation"
    roads = "roads"
    streetlights = "streetlights"
    other = "other"


class Priority(str, enum.Enum):  # noqa: UP042
    high = "high"
    normal = "normal"
    low = "low"


class Status(str, enum.Enum):  # noqa: UP042
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)

    category: Mapped[Category] = mapped_column(SAEnum(Category, name="category_enum"), nullable=False)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority, name="priority_enum"), nullable=False)
    status: Mapped[Status] = mapped_column(
        SAEnum(Status, name="status_enum"), nullable=False, default=Status.open
    )

    ai_summary: Mapped[str | None] = mapped_column(String(140), nullable=True)
    triaged_by: Mapped[str] = mapped_column(String(50), nullable=False)
    triage_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        Index("ix_complaints_status_priority", "status", "priority"),
        Index("ix_complaints_created_at", "created_at"),
    )
