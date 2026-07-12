"""Smart / luxury feature checklist for e-scooters (and optional e-bike extras)."""

FEATURE_GROUPS = (
    ("security", "Security"),
    ("tracking", "Tracking"),
    ("app", "App & connectivity"),
    ("audio", "Audio & phone"),
    ("luxury", "Comfort & premium"),
)

# key -> (label, group, weight for luxury_score)
FEATURE_DEFS = {
    "lock_builtin": ("Built-in lock", "security", 8),
    "lock_cable": ("Cable / U-lock mount", "security", 3),
    "alarm": ("Anti-theft alarm", "security", 6),
    "immobilizer": ("Motor immobilizer", "security", 5),
    "gps_tracking": ("GPS live tracking", "tracking", 12),
    "find_my": ("Find My / location history", "tracking", 10),
    "geofence": ("Geofence alerts", "tracking", 6),
    "companion_app": ("Companion app (iOS/Android)", "app", 8),
    "ride_history": ("Ride stats & history", "app", 4),
    "firmware_ota": ("Over-the-air firmware updates", "app", 5),
    "remote_lock": ("Remote lock / unlock", "app", 6),
    "bluetooth_speaker": ("Built-in Bluetooth speaker", "audio", 7),
    "phone_mount": ("Phone mount included", "audio", 3),
    "suspension": ("Suspension (front or dual)", "luxury", 8),
    "regen_braking": ("Regenerative braking", "luxury", 5),
    "cruise_control": ("Cruise control", "luxury", 4),
    "turn_signals": ("Turn signals", "luxury", 6),
    "keyless_start": ("Keyless / NFC start", "luxury", 4),
    "fold_compact": ("Compact fold", "luxury", 3),
    "ip_rating": ("Water resistance IPX5+", "luxury", 5),
}


def _ip_ok(features: dict) -> bool:
    ip = (features.get("ip_rating") or "").upper()
    if not ip:
        return False
    for level in ("IPX7", "IPX6", "IPX5", "IP54", "IP55", "IP65"):
        if level in ip:
            return True
    return False


def build_feature_checklist(features: dict | None) -> list:
    """Build grouped checklist items from a features dict."""
    feats = features or {}
    items = []
    for key, (label, group, _weight) in FEATURE_DEFS.items():
        if key == "ip_rating":
            ok = _ip_ok(feats)
            val = feats.get("ip_rating") or "—"
        else:
            ok = bool(feats.get(key))
            val = ok
        items.append({
            "key": key,
            "group": group,
            "group_label": dict(FEATURE_GROUPS)[group],
            "label": label,
            "value": val,
            "ok": ok,
        })
    return items


def compute_luxury_score(features: dict | None) -> int:
    feats = features or {}
    score = 0
    for key, (_label, _group, weight) in FEATURE_DEFS.items():
        if key == "ip_rating":
            if _ip_ok(feats):
                score += weight
        elif feats.get(key):
            score += weight
    return min(score, 100)


def format_features_summary(features: dict | None, checklist: list | None = None) -> dict:
    """Highlights for cards: counts per group + top perks."""
    checklist = checklist or build_feature_checklist(features)
    by_group = {g[0]: 0 for g in FEATURE_GROUPS}
    total = 0
    for item in checklist:
        if item["ok"]:
            total += 1
            by_group[item["group"]] = by_group.get(item["group"], 0) + 1
    perks = [item["label"] for item in checklist if item["ok"]][:4]
    return {
        "luxury_score": compute_luxury_score(features),
        "feature_count": total,
        "by_group": by_group,
        "perks_label": " · ".join(perks) if perks else "—",
        "has_app": bool((features or {}).get("companion_app")),
        "has_tracking": bool((features or {}).get("gps_tracking") or (features or {}).get("find_my")),
        "has_security": bool(
            (features or {}).get("lock_builtin")
            or (features or {}).get("alarm")
            or (features or {}).get("immobilizer")
        ),
        "has_audio": bool((features or {}).get("bluetooth_speaker") or (features or {}).get("phone_mount")),
        "is_smart": bool(
            (features or {}).get("companion_app")
            and (
                (features or {}).get("gps_tracking")
                or (features or {}).get("find_my")
                or (features or {}).get("lock_builtin")
            )
        ),
    }