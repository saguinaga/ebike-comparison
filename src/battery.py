CHARGE_LABELS = {
    "onboard": "Onboard plug",
    "removable": "Removable pack",
    "removable_keyed": "Removable (keyed)",
    "none": "N/A",
}


def load_batteries(root) -> dict:
    from pathlib import Path
    import yaml

    path = Path(root) / "config" / "batteries.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("batteries", {})


def battery_wh(voltage_v, capacity_ah) -> int | None:
    if voltage_v and capacity_ah:
        return int(round(float(voltage_v) * float(capacity_ah)))
    return None


def format_battery(bike: dict) -> dict:
    """Build display-friendly battery summary from bike fields."""
    v = bike.get("battery_voltage_v")
    ah = bike.get("battery_capacity_ah")
    wh = bike.get("battery_wh") or battery_wh(v, ah)
    pas = bike.get("battery_range_miles_pas")
    thr = bike.get("battery_range_miles_throttle")
    hrs = bike.get("battery_charge_hours")
    method = bike.get("battery_charge_method") or ""
    notes = bike.get("battery_charge_notes") or ""
    ah_alt = bike.get("battery_capacity_ah_alt")

    if method == "none" or (not v and not ah and not pas):
        return {
            "has_battery": False,
            "capacity_label": "—",
            "range_label": "—",
            "charge_label": "—",
            "summary": "Pedal only",
            "range_miles": None,
            "capacity_ah": None,
            "charge_method": method,
        }

    cap_parts = []
    if v and ah:
        cap = f"{v}V · {ah}Ah"
        if ah_alt:
            cap += f" (or {ah_alt}Ah)"
        if wh:
            cap += f" · {wh}Wh"
        cap_parts.append(cap)
    elif ah:
        cap_parts.append(f"{ah}Ah")

    range_parts = []
    if pas:
        range_parts.append(f"{pas} mi PAS")
    if thr:
        range_parts.append(f"{thr} mi throttle")
    range_label = " · ".join(range_parts) if range_parts else "—"

    charge_parts = []
    if hrs:
        charge_parts.append(f"~{hrs} hr")
    if method and method != "none":
        charge_parts.append(CHARGE_LABELS.get(method, method.replace("_", " ")))
    charge_label = " · ".join(charge_parts) if charge_parts else "—"

    summary = range_label if range_label != "—" else cap_parts[0] if cap_parts else "—"

    return {
        "has_battery": True,
        "capacity_label": cap_parts[0] if cap_parts else "—",
        "range_label": range_label,
        "charge_label": charge_label,
        "charge_notes": notes,
        "summary": summary,
        "range_miles": pas,
        "capacity_ah": ah,
        "battery_wh": wh,
        "charge_method": method,
    }