import json
from pathlib import Path


def load_rules(root: Path) -> dict:
    return json.loads((root / "data" / "legal_rules.json").read_text(encoding="utf-8"))


def evaluate_bike(bike: dict, rider_age: int = 12) -> dict:
    if bike.get("vehicle_type") == "scooter":
        return _evaluate_scooter(bike, rider_age)

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


def _evaluate_scooter(bike: dict, rider_age: int = 12) -> dict:
    max_mph = bike.get("max_speed_mph") or 20
    lights = bike.get("lights") or {}
    legal_for_age = True
    issues = []
    badges = []

    if rider_age < 18:
        issues.append("Helmet required under 18 on streets and bikeways (CVC §21212)")
        badges.append({"type": "warning", "text": "Helmet required"})

    if max_mph > 15:
        issues.append("Many HB paths cap scooters at 10 mph — ride slower near pedestrians")
        badges.append({"type": "warning", "text": "Slow on beach paths"})

    if max_mph > 20:
        issues.append("Over 20 mph — check local scooter ordinances before school commute")
        badges.append({"type": "warning", "text": ">20 mph — verify local rules"})

    if not lights.get("front") or not lights.get("rear"):
        issues.append("Add lights for night rides (CVC §21201 applies to scooters on roads)")

    issues.append("No riding on sidewalks in many HB zones — use bike lanes or streets")
    issues.append("UL-certified battery strongly recommended for charging safety")

    return {
        "legal_for_age": legal_for_age,
        "issues": issues,
        "badges": badges,
        "e_bike_class": "scooter",
    }