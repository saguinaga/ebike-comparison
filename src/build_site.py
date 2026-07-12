import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from .battery import format_battery
from .formatting import format_brake, format_usd
from .images import resolve_bike_images

TIER_LABELS = {
    "budget": "$300–600",
    "value": "$600–1,200",
    "mid": "$1,200–2,000",
    "premium": "$2,000+",
    "scooter": "E-Scooters",
    "baseline": "Baseline",
}


def load_reviewed(root: Path) -> list:
    reviewed = root / "data" / "bikes_reviewed.json"
    raw = root / "data" / "bikes.json"
    path = reviewed if reviewed.exists() else raw
    return json.loads(path.read_text(encoding="utf-8"))


def build(root: Path, min_bikes: int = 18) -> None:
    bikes = load_reviewed(root)
    e_bikes = [b for b in bikes if not b.get("is_baseline")]
    if len(e_bikes) < min_bikes:
        raise SystemExit(f"Need at least {min_bikes} e-bikes, found {len(e_bikes)}")

    bench = yaml.safe_load((root / "config" / "benchmarks.yaml").read_text(encoding="utf-8"))
    legal = json.loads((root / "data" / "legal_rules.json").read_text(encoding="utf-8"))
    safety = json.loads((root / "data" / "safety_research.json").read_text(encoding="utf-8"))
    faq_path = root / "data" / "faq.json"
    faq = json.loads(faq_path.read_text(encoding="utf-8")) if faq_path.exists() else {}

    all_bikes = bikes
    baseline = next((b for b in bikes if b.get("is_baseline")), bench["baseline"])
    rider = bench.get("rider", {})
    main_site = bench.get("main_site_url", "#")

    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    cache_dir = root / "data" / "raw"

    for bike in all_bikes:
        bike["brake_display"] = format_brake(bike.get("brake_type"))
        bike["battery_display"] = format_battery(bike)
        imgs = resolve_bike_images(bike, root, docs, cache_dir, fetch_live=True)
        bike["image_src"] = imgs["image_src"]
        bike["image_gallery"] = imgs["image_gallery"]

    e_bikes = [b for b in all_bikes if not b.get("is_baseline")]
    baseline = next((b for b in all_bikes if b.get("is_baseline")), baseline)
    ebike_count = sum(1 for b in e_bikes if b.get("vehicle_type") != "scooter")
    scooter_count = sum(1 for b in e_bikes if b.get("vehicle_type") == "scooter")

    by_tier = {}
    for b in e_bikes:
        tier = b.get("tier", "other")
        by_tier.setdefault(tier, []).append(b)

    def bike_to_js(b: dict) -> dict:
        legal_b = b.get("legal", {})
        lights = b.get("lights") or {}
        best_url = b.get("best_buy_url")
        if not best_url:
            for src in b.get("sources", []):
                if src.get("url"):
                    best_url = src["url"]
                    break
        return {
            "id": b.get("id"),
            "brand": b.get("brand"),
            "model": b.get("model"),
            "tier": b.get("tier"),
            "tier_label": TIER_LABELS.get(b.get("tier"), b.get("tier")),
            "price": b.get("landed_price_usd") or b.get("price_usd"),
            "price_usd": b.get("price_usd"),
            "landed_price_usd": b.get("landed_price_usd"),
            "safety_score": b.get("safety_score"),
            "safety_checklist": b.get("safety_checklist", []),
            "e_bike_class": b.get("e_bike_class"),
            "legal_for_age": legal_b.get("legal_for_age", True),
            "legal_issues": legal_b.get("issues", []) or legal_b.get("legal_issues", []),
            "max_speed_mph": b.get("max_speed_mph"),
            "brake_type": b.get("brake_type"),
            "brake_display": b.get("brake_display", format_brake(b.get("brake_type"))),
            "motor_w": b.get("motor_w"),
            "lights": lights,
            "ul_certified": bool(b.get("ul_certified")),
            "tire_width_in": b.get("tire_width_in"),
            "colors": b.get("colors", []),
            "image_src": b.get("image_src", ""),
            "image_gallery": b.get("image_gallery", []),
            "vs_baseline": b.get("vs_baseline", {}),
            "friend_recommended": b.get("friend_recommended", False),
            "best_buy_url": best_url,
            "best_buy_platform": b.get("best_buy_platform"),
            "best_buy_delivery": b.get("best_buy_delivery"),
            "price_sources": b.get("price_sources", []),
            "is_baseline": bool(b.get("is_baseline")),
            "url": b.get("url") or best_url,
            "brakes_front": b.get("brakes_front"),
            "brakes_rear": b.get("brakes_rear"),
            "reflectors": b.get("reflectors"),
            "speed_limiter": b.get("speed_limiter"),
            "battery_display": b.get("battery_display", format_battery(b)),
            "battery_range_miles_pas": b.get("battery_range_miles_pas"),
            "battery_range_miles_throttle": b.get("battery_range_miles_throttle"),
            "battery_capacity_ah": b.get("battery_capacity_ah"),
            "battery_voltage_v": b.get("battery_voltage_v"),
            "battery_wh": b.get("battery_wh"),
            "battery_charge_hours": b.get("battery_charge_hours"),
            "battery_charge_method": b.get("battery_charge_method"),
            "battery_charge_notes": b.get("battery_charge_notes"),
            "vehicle_type": b.get("vehicle_type", "ebike"),
            "features": b.get("features", {}),
            "feature_checklist": b.get("feature_checklist", []),
            "feature_display": b.get("feature_display", {}),
            "luxury_score": (b.get("feature_display") or {}).get("luxury_score", 0),
        }

    bikes_for_js = [bike_to_js(b) for b in e_bikes]
    all_bikes_for_js = [bike_to_js(b) for b in all_bikes]

    asset_version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")

    env = Environment(loader=FileSystemLoader(root / "web" / "templates"), autoescape=True)
    env.filters["format_brake"] = format_brake
    env.filters["format_usd"] = format_usd
    template = env.get_template("index.html.j2")
    html = template.render(
        bikes=e_bikes,
        baseline=baseline,
        by_tier=by_tier,
        tier_labels=TIER_LABELS,
        rider=rider,
        legal=legal,
        safety=safety,
        faq=faq,
        legal_json=json.dumps(legal),
        safety_json=json.dumps(safety),
        faq_json=json.dumps(faq),
        main_site_url=main_site,
        generated_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        asset_version=asset_version,
        ebike_count=ebike_count,
        scooter_count=scooter_count,
        bikes_json=json.dumps(bikes_for_js),
        all_bikes_json=json.dumps(all_bikes_for_js),
        default_baseline_id=baseline.get("id", "firmstrong-urban-lady"),
        tier_labels_json=json.dumps(TIER_LABELS),
    )

    (docs / "index.html").write_text(html, encoding="utf-8")

    for asset in ("styles.css", "app.js"):
        src = root / "web" / asset
        if not src.exists():
            continue
        stem, ext = asset.rsplit(".", 1)
        versioned = f"{stem}.{asset_version}.{ext}"
        shutil.copy(src, docs / versioned)
        if asset == "app.js":
            shim = (
                "/* Loader for cached index.html still requesting app.js */\n"
                f'(function(){{var s=document.createElement("script");'
                f's.src="{versioned}";s.defer=true;document.head.appendChild(s);}})();\n'
            )
            (docs / asset).write_text(shim, encoding="utf-8")
        else:
            (docs / asset).write_text(f'/* Loader for cached styles.css */\n@import url("{versioned}");\n', encoding="utf-8")