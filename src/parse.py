import copy
import json
from pathlib import Path

import yaml

from .colors import normalize_colors
from .compare_pedal import compare_to_baseline
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


def parse_all(root: Path, scrape_live: bool = True) -> list:
    bikes_cfg, bench_cfg = load_config(root)
    baseline = bench_cfg["baseline"]
    rider = bench_cfg.get("rider", {})
    cache_dir = root / "data" / "raw"
    results = []

    # Parse baseline
    baseline_bike = {**baseline, "is_baseline": True, "tier": "baseline"}
    if scrape_live:
        try:
            url = baseline["url"]
            html = fetch_url(url, cache_dir)
            parsed = PARSERS["firmstrong"](html, {"baseline": baseline})
            baseline_bike = _merge(baseline_bike, parsed)
        except Exception:
            pass
    results.append(baseline_bike)

    for entry in bikes_cfg.get("bikes", []):
        bike = copy.deepcopy(entry)
        bike.pop("manual", None)
        manual = entry.get("manual", {})

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
        bike["colors"] = normalize_colors(bike.get("colors", []))
        bike.update(compute_landed_prices({**entry, **bike}))
        bike["safety_score"] = compute_safety_score(bike)
        bike["safety_checklist"] = build_checklist(bike)
        bike["legal"] = evaluate_bike(bike, rider.get("age", 12))
        bike["vs_baseline"] = compare_to_baseline(bike, baseline_bike)
        bike["friend_recommended"] = entry.get("friend_recommended", False)
        results.append(bike)

    return results


def save_bikes(root: Path, bikes: list, filename: str = "bikes.json") -> Path:
    out = root / "data" / filename
    out.write_text(json.dumps(bikes, indent=2), encoding="utf-8")
    return out