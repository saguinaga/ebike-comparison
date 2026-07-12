PLATFORM_LABELS = {
    "amazon": "Amazon",
    "aliexpress": "AliExpress",
    "manufacturer": "Direct",
    "manual": "Listed",
}

DELIVERY_NOTES = {
    "amazon": "Prime ~1–3 days",
    "aliexpress": "~2–4 weeks",
    "manufacturer": "Direct ship",
}


def _source_price(src: dict, bike: dict, manual: dict) -> tuple[float, float]:
    """Return (item_price, shipping) for a source entry."""
    item = src.get("price_usd")
    if item is None:
        item = bike.get("price_usd") or manual.get("price_usd") or 0

    ship = src.get("shipping_usd")
    if ship is None:
        platform = src.get("platform", "")
        if platform == "aliexpress":
            ship = manual.get("shipping_estimate_usd", 120)
        elif platform == "amazon":
            ship = 0
        else:
            ship = manual.get("shipping_estimate_usd", 0)

    return float(item or 0), float(ship or 0)


def compute_landed_prices(bike: dict) -> dict:
    manual = bike.get("manual", {})
    entries = []

    for src in bike.get("sources", []):
        platform = src.get("platform", "unknown")
        url = src.get("url")
        if not url:
            continue
        item, ship = _source_price(src, bike, manual)
        landed = item + ship
        entries.append({
            "platform": platform,
            "platform_label": PLATFORM_LABELS.get(platform, platform.title()),
            "url": url,
            "item_price_usd": item,
            "shipping_usd": ship,
            "landed_usd": landed,
            "delivery_note": DELIVERY_NOTES.get(platform, "Varies"),
            "rewards_note": (
                "5% back on some Chase/Amazon cards"
                if platform == "amazon" else None
            ),
            "is_search_url": "/s?" in url or "wholesale" in url or "/w/" in url,
        })

    if not entries:
        base = bike.get("price_usd") or manual.get("price_usd") or 0
        ship = manual.get("shipping_estimate_usd", 0)
        if base:
            entries.append({
                "platform": "manual",
                "platform_label": "Listed",
                "url": bike.get("url"),
                "item_price_usd": base,
                "shipping_usd": ship,
                "landed_usd": base + ship,
                "delivery_note": "Price estimate",
                "rewards_note": None,
                "is_search_url": False,
            })

    entries.sort(key=lambda e: e.get("landed_usd") or 99999)
    best = entries[0] if entries else None

    return {
        "price_sources": entries,
        "landed_price_usd": best["landed_usd"] if best else None,
        "best_buy_url": best["url"] if best else None,
        "best_buy_platform": best["platform_label"] if best else None,
        "best_buy_shipping_usd": best["shipping_usd"] if best else 0,
        "best_buy_delivery": best["delivery_note"] if best else None,
    }