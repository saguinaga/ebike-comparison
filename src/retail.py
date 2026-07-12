"""Merge Target and local Huntington Beach retail sources into product sources."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_retail_config(root: Path | None = None) -> dict:
    path = (root or ROOT) / "config" / "retail_sources.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _retailer_defaults(cfg: dict, retailer_key: str) -> dict:
    retailers = cfg.get("retailers", {})
    meta = retailers.get(retailer_key, {})
    return {
        "platform": meta.get("platform", "local"),
        "retailer": retailer_key,
        "retailer_label": meta.get("label", retailer_key),
        "delivery_note": meta.get("delivery_note"),
    }


def _normalize_entry(raw: dict, cfg: dict) -> dict | None:
    if raw.get("skip"):
        return None
    retailer_key = raw.get("retailer", "")
    meta = _retailer_defaults(cfg, retailer_key)
    url = raw.get("url")
    if not url and retailer_key:
        url = (cfg.get("retailers", {}).get(retailer_key) or {}).get("url")
    if not url:
        return None
    entry = {
        "platform": meta["platform"],
        "url": url,
        "retailer": retailer_key,
        "retailer_label": meta["retailer_label"],
        "in_store_only": bool(raw.get("in_store_only", True)),
        "note": raw.get("note"),
    }
    if raw.get("price_usd") is not None:
        entry["price_usd"] = raw["price_usd"]
        entry["in_store_only"] = False
    if raw.get("shipping_usd") is not None:
        entry["shipping_usd"] = raw["shipping_usd"]
    return entry


def augment_sources(
    product_id: str,
    vehicle_type: str,
    sources: list | None,
    cfg: dict | None = None,
) -> list:
    """Return sources with Target / local HB channels appended (no duplicates)."""
    cfg = cfg or load_retail_config()
    if not cfg:
        return list(sources or [])

    out = list(sources or [])
    seen_urls = {s.get("url") for s in out if s.get("url")}

    def add(raw: dict) -> None:
        entry = _normalize_entry(raw, cfg)
        if not entry or entry["url"] in seen_urls:
            return
        seen_urls.add(entry["url"])
        out.append(entry)

    for raw in (cfg.get("products", {}).get(product_id) or []):
        add(raw)

    kind = "scooter" if vehicle_type == "scooter" else "ebike"
    for raw in (cfg.get("defaults", {}).get(kind) or []):
        add(raw)

    return out