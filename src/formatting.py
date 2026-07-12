BRAKE_DISPLAY = {
    "hydraulic_disc": {
        "icon": "",
        "label": "Hydraulic Disc",
        "css_class": "brake-hydraulic_disc",
        "glyph": True,
    },
    "mechanical_disc": {
        "icon": "",
        "label": "Mechanical Disc",
        "css_class": "brake-mechanical_disc",
        "glyph": True,
    },
    "rim": {"icon": "⭕", "label": "Rim Brake", "css_class": "brake-rim"},
    "coaster": {"icon": "↩️", "label": "Coaster", "css_class": "brake-coaster"},
}


def format_brake(brake_type: str | None) -> dict:
    key = (brake_type or "rim").lower()
    info = BRAKE_DISPLAY.get(key, {"icon": "❓", "label": key.replace("_", " ").title()})
    return {
        "icon": info["icon"],
        "label": info["label"],
        "key": key,
        "css_class": info.get("css_class", ""),
        "glyph": info.get("glyph", False),
    }


def format_usd(amount) -> str:
    if amount is None:
        return "—"
    try:
        val = float(amount)
        if val == int(val):
            return f"${int(val):,}"
        return f"${val:,.2f}"
    except (TypeError, ValueError):
        return "—"