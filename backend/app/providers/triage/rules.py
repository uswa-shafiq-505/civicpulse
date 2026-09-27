from app.models import Category, Priority
from app.schemas import TriageResult

_CATEGORY_KEYWORDS: dict[Category, list[str]] = {
    Category.water: ["water", "pipe", "leak", "burst", "sewer", "flood"],
    Category.electricity: ["electric", "power", "wire", "transformer", "shock", "electrocut"],
    Category.sanitation: ["garbage", "trash", "sewage", "waste", "sanitation", "drain"],
    Category.roads: ["road", "pothole", "street ", "asphalt", "traffic"],
    Category.streetlights: ["streetlight", "street light", "lamp post", "lightpole"],
}

_HIGH_PRIORITY_KEYWORDS = [
    "flood", "danger", "fire", "accident", "electrocut", "burst", "emergency",
    "collapse", "injur", "death", "dying",
]


class RuleBasedTriage:
    name = "rules"

    def triage(self, text: str, location: str) -> TriageResult:
        lowered = text.lower()

        category = Category.other
        for cat, keywords in _CATEGORY_KEYWORDS.items():
            if any(k in lowered for k in keywords):
                category = cat
                break

        priority = Priority.normal
        if any(k in lowered for k in _HIGH_PRIORITY_KEYWORDS):
            priority = Priority.high
        elif len(text.strip()) < 30:
            priority = Priority.low

        summary = text.strip().replace("\n", " ")[:137]
        if len(text.strip()) > 137:
            summary += "..."

        return TriageResult(category=category, priority=priority, summary=summary, confidence=0.5)
