"""Idempotent seed: loads >=30 realistic complaints. Running it twice does
not duplicate rows -- each seed complaint is keyed by a deterministic id
derived from its text, and we upsert (insert-if-absent) by that id.
"""
import hashlib
import uuid

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Category, Complaint, Priority, Status

_COMPLAINTS: list[tuple[str, str, Category, Priority]] = [
    ("Water line burst near Saddar, street flooding since this morning.", "Saddar, Rawalpindi", Category.water, Priority.high),
    ("Streetlight has been off for three nights on the main avenue.", "F-10 Markaz, Islamabad", Category.streetlights, Priority.low),
    ("Garbage overflowing near the school gate for a week now.", "G-9/4, Islamabad", Category.sanitation, Priority.normal),
    ("Large pothole on the main road causing accidents at night.", "Murree Road, Rawalpindi", Category.roads, Priority.high),
    ("Electric wire hanging loose near the park, kids play there.", "Bahria Town Phase 4, Rawalpindi", Category.electricity, Priority.high),
    ("Sewage water entering the house since yesterday, very bad smell.", "Dhoke Kashmirian, Rawalpindi", Category.sanitation, Priority.high),
    ("No streetlights on our entire block, feels unsafe after dark.", "I-8/3, Islamabad", Category.streetlights, Priority.normal),
    ("Small pothole forming near the roundabout, not urgent yet.", "Blue Area, Islamabad", Category.roads, Priority.low),
    ("Transformer making loud buzzing noise and sparking occasionally.", "Wah Cantt", Category.electricity, Priority.high),
    ("Garbage truck has not come to our street in over two weeks.", "Satellite Town, Rawalpindi", Category.sanitation, Priority.normal),
    ("Water pressure extremely low in our area since Monday.", "PWD Housing Society, Islamabad", Category.water, Priority.normal),
    ("Road markings faded completely near the school crossing.", "G-11, Islamabad", Category.roads, Priority.normal),
    ("Frequent power cuts every evening for the last month.", "Chaklala Scheme 3, Rawalpindi", Category.electricity, Priority.normal),
    ("Drain blocked and overflowing onto the main street.", "Committee Chowk, Rawalpindi", Category.sanitation, Priority.high),
    ("One streetlight flickers constantly, might need replacement.", "E-11, Islamabad", Category.streetlights, Priority.low),
    ("Water tanker required urgently, no supply for three days.", "Taxila", Category.water, Priority.high),
    ("Pothole filled with rainwater, hard to see at night, risky.", "Rawal Road, Rawalpindi", Category.roads, Priority.high),
    ("Exposed electrical cable near the bus stop, very dangerous.", "Faizabad, Rawalpindi", Category.electricity, Priority.high),
    ("Garbage bin missing from our street corner for months.", "F-7 Markaz, Islamabad", Category.sanitation, Priority.low),
    ("Streetlights in the whole society are off, contractor unresponsive.", "Bahria Town Phase 8, Rawalpindi", Category.streetlights, Priority.normal),
    ("Water leaking from a joint under the road, wasting a lot of water.", "Adiala Road, Rawalpindi", Category.water, Priority.normal),
    ("Speed breaker damaged badly, causing vehicles to swerve suddenly.", "Airport Road, Rawalpindi", Category.roads, Priority.normal),
    ("Meter box sparked once, worried about a fire hazard now.", "G-6, Islamabad", Category.electricity, Priority.high),
    ("Open manhole near the market, someone could fall in easily.", "Raja Bazaar, Rawalpindi", Category.sanitation, Priority.high),
    ("Streetlight pole leaning dangerously after last week's storm.", "H-8, Islamabad", Category.streetlights, Priority.high),
    ("Water supply timing changed with no prior notice to residents.", "Chaklala, Rawalpindi", Category.water, Priority.low),
    ("Road under construction blocking the only access route for a week.", "Peshawar Road, Rawalpindi", Category.roads, Priority.normal),
    ("Electricity bill meter reading seems faulty, need it checked.", "I-10, Islamabad", Category.electricity, Priority.low),
    ("Dead animal left uncollected on the roadside for two days.", "Sadiqabad, Rawalpindi", Category.sanitation, Priority.high),
    ("General query about the complaint portal, not urgent, just curious.", "Online", Category.other, Priority.low),
    ("Streetlights near the park have been fixed, thank you, closing loop.", "F-6, Islamabad", Category.streetlights, Priority.low),
    ("Water contamination suspected, tastes and smells odd since today.", "Westridge, Rawalpindi", Category.water, Priority.high),
]


def _deterministic_id(text: str) -> str:
    digest = hashlib.sha256(text.encode()).hexdigest()
    return str(uuid.UUID(digest[:32]))


def run() -> None:
    db = SessionLocal()
    inserted, skipped = 0, 0
    try:
        for text, location, category, priority in _COMPLAINTS:
            seed_id = _deterministic_id(text)
            existing = db.execute(select(Complaint).where(Complaint.id == seed_id)).scalar_one_or_none()
            if existing:
                skipped += 1
                continue

            db.add(Complaint(
                id=seed_id,
                text=text,
                location=location,
                category=category,
                priority=priority,
                status=Status.open,
                ai_summary=text[:137] + ("..." if len(text) > 137 else ""),
                triaged_by="rules:seed",
                triage_latency_ms=0,
            ))
            inserted += 1
        db.commit()
    finally:
        db.close()

    print(f"seed complete: inserted={inserted} skipped(existing)={skipped} total_defined={len(_COMPLAINTS)}")


if __name__ == "__main__":
    run()
