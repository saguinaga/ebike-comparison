BRAKE_SCORES = {
    "coaster": 5,
    "rim": 8,
    "mechanical_disc": 18,
    "hydraulic_disc": 25,
}

CHECKLIST_FIELDS = [
    ("brake_type", "Brake type"),
    ("brakes_front", "Front brake"),
    ("brakes_rear", "Rear brake"),
    ("lights.front", "Front light"),
    ("lights.rear", "Rear light"),
    ("reflectors", "Reflectors"),
    ("ul_certified", "UL battery cert"),
    ("motor_cutoff", "Motor cut-off on brake"),
    ("tire_width_in", "Tire width"),
    ("speed_limiter", "Speed limiter"),
]


def _get_nested(obj: dict, path: str):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def build_checklist(bike: dict) -> list:
    lights = bike.get("lights") or {}
    items = [
        {"key": "brake_type", "label": "Brake type", "value": bike.get("brake_type"), "ok": bike.get("brake_type") in ("mechanical_disc", "hydraulic_disc")},
        {"key": "front_brake", "label": "Front brake", "value": bike.get("brakes_front", False), "ok": bool(bike.get("brakes_front"))},
        {"key": "rear_brake", "label": "Rear brake", "value": bike.get("brakes_rear", True), "ok": bool(bike.get("brakes_rear", True))},
        {"key": "front_light", "label": "Front light", "value": lights.get("front"), "ok": bool(lights.get("front"))},
        {"key": "rear_light", "label": "Rear light", "value": lights.get("rear"), "ok": bool(lights.get("rear"))},
        {"key": "reflectors", "label": "Reflectors", "value": bike.get("reflectors"), "ok": bool(bike.get("reflectors", False))},
        {"key": "ul_cert", "label": "UL battery cert", "value": bike.get("ul_certified"), "ok": bool(bike.get("ul_certified"))},
        {"key": "tires", "label": "Tire width ≥ 2.0\"", "value": bike.get("tire_width_in"), "ok": (bike.get("tire_width_in") or 0) >= 2.0},
        {"key": "speed_limiter", "label": "Speed limiter", "value": bike.get("speed_limiter"), "ok": bool(bike.get("speed_limiter", bike.get("max_speed_mph", 99) <= 20))},
    ]
    return items


def compute_safety_score(bike: dict) -> int:
    score = 0
    brake = bike.get("brake_type", "rim")
    score += BRAKE_SCORES.get(brake, 5)

    lights = bike.get("lights") or {}
    if lights.get("front"):
        score += 10
    if lights.get("rear"):
        score += 10
    if bike.get("reflectors"):
        score += 5
    if (bike.get("tire_width_in") or 0) >= 2.4:
        score += 5
    max_spd = bike.get("max_speed_mph") or 20
    if max_spd <= 20:
        score += 10
    elif max_spd <= 28:
        score += 5
    if bike.get("ul_certified"):
        score += 5
    if bike.get("brakes_front"):
        score += 5
    return min(score, 100)