from .formatting import format_brake

BRAKE_SCORES = {
    "coaster": 5,
    "rim": 8,
    "mechanical_disc": 18,
    "hydraulic_disc": 25,
}

CHECKLIST_ROW_LABELS = {
    "brake_type": "Brakes",
    "front_brake": "Front brake",
    "rear_brake": "Rear brake",
    "front_light": "Front light",
    "rear_light": "Rear light",
    "reflectors": "Reflectors",
    "ul_cert": "UL battery cert",
    "tires": "Tire width ≥ 2.0\"",
    "speed_limiter": "Speed limiter",
}


def _get_nested(obj: dict, path: str):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _check_item(key: str, label: str, value, ok: bool) -> dict:
    return {
        "key": key,
        "row_label": CHECKLIST_ROW_LABELS.get(key, label),
        "label": label,
        "value": value,
        "ok": ok,
    }


def build_checklist(bike: dict) -> list:
    lights = bike.get("lights") or {}
    brake_info = format_brake(bike.get("brake_type"))
    tire_w = bike.get("tire_width_in")
    return [
        _check_item(
            "brake_type",
            brake_info["label"],
            bike.get("brake_type"),
            bike.get("brake_type") in ("mechanical_disc", "hydraulic_disc"),
        ),
        _check_item("front_brake", "Front brake", bike.get("brakes_front", False), bool(bike.get("brakes_front"))),
        _check_item("rear_brake", "Rear brake", bike.get("brakes_rear", True), bool(bike.get("brakes_rear", True))),
        _check_item("front_light", "Front light", lights.get("front"), bool(lights.get("front"))),
        _check_item("rear_light", "Rear light", lights.get("rear"), bool(lights.get("rear"))),
        _check_item("reflectors", "Reflectors", bike.get("reflectors"), bool(bike.get("reflectors", False))),
        _check_item("ul_cert", "UL battery cert", bike.get("ul_certified"), bool(bike.get("ul_certified"))),
        _check_item(
            "tires",
            f'Tires {tire_w}" wide' if tire_w else "Wide tires (≥ 2.0\")",
            tire_w,
            (tire_w or 0) >= 2.0,
        ),
        _check_item(
            "speed_limiter",
            "Speed limiter",
            bike.get("speed_limiter"),
            bool(bike.get("speed_limiter", bike.get("max_speed_mph", 99) <= 20)),
        ),
    ]


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