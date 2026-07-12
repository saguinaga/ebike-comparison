import copy
import json
from pathlib import Path

import yaml

from .battery import battery_wh, load_batteries
from .colors import normalize_colors
from .compare_pedal import compare_to_baseline
from .features import build_feature_checklist, format_features_summary
from .legal_compliance import evaluate_bike
from .parsers import PARSERS
from .pricing import compute_landed_prices
from .safety_score import build_checklist, compute_safety_score
from .scrape import fetch_url


def _merge(base: dict, overlay: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in overlay.items():
        if k == "field_confidence":
            out.setdefault("field_confidence", {}).update(v)
        elif v is not None:
            out[k] = v
    return out


def load_config(root: Path) -> tuple:
    bikes_cfg = yaml.safe_load((root / "config" / "bikes.yaml").read_text(encoding="utf-8"))
    bench_cfg = yaml.safe_load((root / "config" / "benchmarks.yaml").read_text(encoding="utf-8"))
    return bikes_cfg, bench_cfg


def load_scooters(root: Path) -> list:
    path = root / "config" / "scooters.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("scooters", [])


def _apply_battery_spec(bike: dict, spec: dict) -> None:
    if not spec:
        return
    mapping = {
        "voltage_v": "battery_voltage_v",
        "capacity_ah": "battery_capacity_ah",
        "capacity_ah_alt": "battery_capacity_ah_alt",
        "range_miles_pas": "battery_range_miles_pas",
        "range_miles_throttle": "battery_range_miles_throttle",
        "charge_hours": "battery_charge_hours",
        "charge_method": "battery_charge_method",
        "charge_notes": "battery_charge_notes",
    }
    for src, dst in mapping.items():
        if spec.get(src) is not None:
            bike[dst] = spec[src]
    bike["battery_wh"] = battery_wh(bike.get("battery_voltage_v"), bike.get("battery_capacity_ah"))


def load_image_galleries(root: Path) -> dict:
    path = root / "config" / "image_galleries.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("galleries", {})


def parse_all(root: Path, scrape_live: bool = True) -> list:
    bikes_cfg, bench_cfg = load_config(root)
    galleries = load_image_galleries(root)
    batteries = load_batteries(root)
    baseline = bench_cfg["baseline"]
    rider = bench_cfg.get("rider", {})
    cache_dir = root / "data" / "raw"
    results = []

    # Parse baseline
    baseline_bike = {**baseline, "is_baseline": True, "tier": "baseline"}
    if baseline_bike.get("id") in galleries:
        baseline_bike = _merge(baseline_bike, galleries[baseline_bike["id"]])
    if baseline_bike.get("id") in batteries:
        _apply_battery_spec(baseline_bike, batteries[baseline_bike["id"]])
    if scrape_live:
        try:
            url = baseline["url"]
            html = fetch_url(url, cache_dir)
            parsed = PARSERS["firmstrong"](html, {"baseline": baseline})
            baseline_bike = _merge(baseline_bike, parsed)
        except Exception:
            pass
    results.append(baseline_bike)

    all_entries = list(bikes_cfg.get("bikes", [])) + load_scooters(root)

    for entry in all_entries:
        bike = copy.deepcopy(entry)
        bike.pop("manual", None)
        manual = entry.get("manual", {})
        if not bike.get("vehicle_type"):
            bike["vehicle_type"] = "ebike"

        parser_name = entry.get("parser", "generic")
        parser = PARSERS.get(parser_name, PARSERS["generic"])

        if scrape_live:
            for src in entry.get("sources", []):
                if src.get("platform") == "manufacturer" and src.get("url"):
                    try:
                        html = fetch_url(src["url"], cache_dir)
                        parsed = parser(html, entry)
                        bike = _merge(bike, parsed)
                    except Exception:
                        pass
                    break

        bike = _merge(bike, manual)
        if bike.get("id") in galleries:
            bike = _merge(bike, galleries[bike["id"]])
        if bike.get("id") in batteries:
            _apply_battery_spec(bike, batteries[bike["id"]])
        bike["colors"] = normalize_colors(bike.get("colors", []))
        bike.update(compute_landed_prices({**entry, **bike}))
        bike["safety_score"] = compute_safety_score(bike)
        bike["safety_checklist"] = build_checklist(bike)
        if bike.get("features"):
            bike["feature_checklist"] = build_feature_checklist(bike["features"])
            bike["feature_display"] = format_features_summary(bike["features"], bike["feature_checklist"])
        else:
            bike["feature_checklist"] = []
            bike["feature_display"] = format_features_summary({})
        bike["legal"] = evaluate_bike(bike, rider.get("age", 12))
        bike["vs_baseline"] = compare_to_baseline(bike, baseline_bike)
        bike["friend_recommended"] = entry.get("friend_recommended", False)
        results.append(bike)

    return results


def save_bikes(root: Path, bikes: list, filename: str = "bikes.json") -> Path:
    out = root / "data" / filename
    out.write_text(json.dumps(bikes, indent=2), encoding="utf-8")
    return out