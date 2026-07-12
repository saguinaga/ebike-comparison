#!/usr/bin/env python3
"""Compare config source prices vs live manufacturer scrape."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.parse import parse_all  # noqa: E402


def load_config_prices() -> dict[str, float]:
    prices: dict[str, float] = {}
    for rel in ("config/bikes.yaml", "config/scooters.yaml"):
        data = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
        items = data.get("bikes") or data.get("scooters") or []
        for item in items:
            for src in item.get("sources", []):
                if src.get("platform") == "manufacturer" and src.get("price_usd") is not None:
                    prices[item["id"]] = float(src["price_usd"])
                    break
    return prices


def main() -> int:
    config_prices = load_config_prices()
    bikes = parse_all(ROOT, scrape_live=True)
    mismatches = []
    for bike in bikes:
        if bike.get("is_baseline"):
            continue
        bid = bike["id"]
        live = bike.get("landed_price_usd")
        if live is None:
            continue
        cfg = config_prices.get(bid)
        if cfg is None:
            continue
        delta = abs(live - cfg)
        if delta >= 25:
            mismatches.append((bid, cfg, live, delta))

    mismatches.sort(key=lambda x: x[3], reverse=True)
    for bid, cfg, live, delta in mismatches:
        print(f"MISMATCH ${cfg:.0f} -> ${live:.0f} (Δ${delta:.0f})  {bid}")
    print("---")
    print(f"Checked {len(config_prices)} priced sources; mismatches: {len(mismatches)}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())