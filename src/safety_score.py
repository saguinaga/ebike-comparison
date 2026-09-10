from .formatting import format_brake

BRAKE_SCORES = {
    "coaster": 0,
    "rim": 4,
    "mechanical_disc": 12,
    "hydraulic_disc": 24,
    "electronic_disc": 18,
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


def build_scooter_checklist(bike: dict) -> list:
    lights = bike.get("lights") or {}
    brake_info = format_brake(bike.get("brake_type"))
    feats = bike.get("features") or {}
    ip = (feats.get("ip_rating") or "").upper()
    ip_ok = any(x in ip for x in ("IPX5", "IPX6", "IPX7", "IP54", "IP55", "IP65"))
    return [
        _check_item(
            "brake_type",
            brake_info["label"],
            bike.get("brake_type"),
            bike.get("brake_type") in ("mechanical_disc", "hydraulic_disc", "electronic_disc"),
        ),
        _check_item("front_light", "Front light", lights.get("front"), bool(lights.get("front"))),
        _check_item("rear_light", "Rear light", lights.get("rear"), bool(lights.get("rear"))),
        _check_item("ul_cert", "UL battery cert", bike.get("ul_certified"), bool(bike.get("ul_certified"))),
        _check_item("speed_limiter", "≤20 mph", bike.get("max_speed_mph"), (bike.get("max_speed_mph") or 99) <= 20),
        _check_item("ip_rating", "Water resistant", feats.get("ip_rating"), ip_ok),
        _check_item("reflectors", "Reflectors", bike.get("reflectors", True), True),
    ]


def build_checklist(bike: dict) -> list:
    if bike.get("vehicle_type") == "scooter":
        return build_scooter_checklist(bike)
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


def _has_front_brake(bike: dict) -> bool:
    if bike.get("brakes_front") is True:
        return True
    if bike.get("brakes_front") is False:
        return False
    return bike.get("brake_type") in ("mechanical_disc", "hydraulic_disc", "electronic_disc")


def compute_safety_score(bike: dict) -> int:
    """Family-weighted score. UL, hydraulic brakes, and 20 mph cap move the needle.

    Typical spread: cruiser baseline ~20, mid Class 2 with UL ~75-88, Class 3 without limiter ~55-65.
    """
    if bike.get("vehicle_type") == "scooter":
        return _compute_scooter_safety_score(bike)
    score = 4
    brake = bike.get("brake_type", "rim")
    score += BRAKE_SCORES.get(brake, 4)
    if _has_front_brake(bike):
        score += 8
    lights = bike.get("lights") or {}
    if lights.get("front"):
        score += 7
    if lights.get("rear"):
        score += 7
    if bike.get("reflectors"):
        score += 4
    tire_w = bike.get("tire_width_in") or 0
    if tire_w >= 2.4:
        score += 6
    elif tire_w >= 2.0:
        score += 3
    if bike.get("ul_certified"):
        score += 20
    max_spd = bike.get("max_speed_mph") or 20
    if max_spd <= 15:
        score += 12
    elif max_spd <= 20:
        score += 10
    elif max_spd <= 28:
        score += 2
    cls = bike.get("e_bike_class")
    if cls == 3 or str(cls) == "3":
        score -= 8
    if bike.get("speed_limiter") is True:
        score += 6
    return max(5, min(score, 100))


def _compute_scooter_safety_score(bike: dict) -> int:
    score = 10
    brake = bike.get("brake_type", "rim")
    score += BRAKE_SCORES.get(brake, 4)
    lights = bike.get("lights") or {}
    if lights.get("front"):
        score += 10
    if lights.get("rear"):
        score += 10
    if bike.get("ul_certified"):
        score += 22
    max_spd = bike.get("max_speed_mph") or 20
    if max_spd <= 15:
        score += 12
    elif max_spd <= 20:
        score += 10
    feats = bike.get("features") or {}
    ip = (feats.get("ip_rating") or "").upper()
    if any(x in ip for x in ("IPX5", "IPX6", "IPX7", "IP54", "IP55", "IP65")):
        score += 8
    if feats.get("alarm") or feats.get("lock_builtin"):
        score += 6
    return max(5, min(score, 100))