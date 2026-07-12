import json
from pathlib import Path


def load_rules(root: Path) -> dict:
    return json.loads((root / "data" / "legal_rules.json").read_text(encoding="utf-8"))


def evaluate_bike(bike: dict, rider_age: int = 12) -> dict:
    cls = bike.get("e_bike_class")
    max_mph = bike.get("max_speed_mph") or 20
    lights = bike.get("lights") or {}

    legal_for_age = True
    issues = []
    badges = []

    if cls == 3 or (isinstance(cls, str) and str(cls) == "3"):
        if rider_age < 16:
            legal_for_age = False
            issues.append("Class 3 — illegal for under 16 in California (CVC §21213)")
            badges.append({"type": "danger", "text": "Illegal at age 12"})

    if rider_age < 18:
        badges.append({"type": "info", "text": "Helmet required (under 18)"})

    if not lights.get("front") or not lights.get("rear"):
        issues.append("Missing integrated lights — add before night rides (CVC §21201)")
        badges.append({"type": "warning", "text": "Add lights for night"})

    if max_mph > 10:
        issues.append("Exceeds 10 mph HB beach/park path limit — slow down on paths")

    return {
        "legal_for_age": legal_for_age,
        "issues": issues,
        "badges": badges,
        "e_bike_class": cls,
    }