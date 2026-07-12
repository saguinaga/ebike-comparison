"""Apply live-scraped prices onto manufacturer source entries."""

from __future__ import annotations

MIN_CONFIDENCE = 0.8
MAX_DEVIATION = 0.55  # reject scrapes >55% away from configured price


def _config_manufacturer_price(entry_sources: list) -> float | None:
    for src in entry_sources:
        if src.get("platform") == "manufacturer" and src.get("price_usd") is not None:
            return float(src["price_usd"])
    return None


def apply_scraped_prices(bike: dict, entry_sources: list | None = None) -> None:
    """Overwrite manufacturer source prices when scrape returned a confident price."""
    scraped = bike.get("price_usd")
    if scraped is None:
        return
    confidence = (bike.get("field_confidence") or {}).get("price_usd", 0)
    if confidence < MIN_CONFIDENCE:
        return

    config_price = _config_manufacturer_price(entry_sources or [])
    if config_price:
        delta = abs(float(scraped) - config_price) / config_price
        if delta > MAX_DEVIATION:
            return

    for src in bike.get("sources", []):
        if src.get("platform") != "manufacturer":
            continue
        if src.get("in_store_only"):
            continue
        src["price_usd"] = round(float(scraped), 2)
        break