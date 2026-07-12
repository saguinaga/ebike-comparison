PLATFORM_LABELS = {
    "amazon": "Amazon",
    "aliexpress": "AliExpress",
    "manufacturer": "Direct",
    "manual": "Listed",
    "target": "Target",
    "local": "Local (HB)",
}

DELIVERY_NOTES = {
    "amazon": "Prime ~1–3 days",
    "aliexpress": "~2–4 weeks",
    "manufacturer": "Direct ship",
    "target": "Target · pick up in HB or ship",
    "local": "In-store · Huntington Beach",
}


def is_untrusted_buy_url(url: str | None) -> bool:
    """Search pages and wholesale listings are not acceptable buy links."""
    if not url:
        return True
    lower = url.lower()
    if "/s?" in lower or "wholesale" in lower or "/w/" in lower:
        return True
    if "search" in lower and ("amazon" in lower or "aliexpress" in lower):
        return True
    return False


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
        if not url or is_untrusted_buy_url(url):
            continue
        in_store = bool(src.get("in_store_only")) or (
            platform in ("target", "local") and src.get("price_usd") is None
        )
        label = src.get("retailer_label") or PLATFORM_LABELS.get(platform, platform.title())
        delivery = src.get("delivery_note") or DELIVERY_NOTES.get(platform, "Varies")
        if src.get("note"):
            delivery = f"{delivery} — {src['note']}"

        if in_store:
            entries.append({
                "platform": platform,
                "platform_label": label,
                "retailer": src.get("retailer"),
                "url": url,
                "item_price_usd": None,
                "shipping_usd": 0,
                "landed_usd": None,
                "delivery_note": delivery,
                "rewards_note": None,
                "is_search_url": False,
                "in_store_only": True,
                "price_display": "Check store",
            })
            continue

        item, ship = _source_price(src, bike, manual)
        landed = item + ship
        entries.append({
            "platform": platform,
            "platform_label": label,
            "retailer": src.get("retailer"),
            "url": url,
            "item_price_usd": item,
            "shipping_usd": ship,
            "landed_usd": landed,
            "delivery_note": delivery,
            "rewards_note": (
                "5% back on some Chase/Amazon cards"
                if platform == "amazon" else None
            ),
            "is_search_url": False,
            "in_store_only": False,
        })

    priced = [e for e in entries if e.get("landed_usd") is not None]
    in_store = [e for e in entries if e.get("in_store_only")]

    if not priced:
        base = bike.get("price_usd") or manual.get("price_usd") or 0
        ship = manual.get("shipping_estimate_usd", 0)
        if base:
            listed_url = bike.get("url")
            if is_untrusted_buy_url(listed_url):
                listed_url = None
            priced.append({
                "platform": "manual",
                "platform_label": "Listed",
                "url": listed_url,
                "item_price_usd": base,
                "shipping_usd": ship,
                "landed_usd": base + ship,
                "delivery_note": "Price estimate",
                "rewards_note": None,
                "is_search_url": False,
                "in_store_only": False,
            })

    priced.sort(key=lambda e: e.get("landed_usd") or 99999)
    in_store.sort(key=lambda e: e.get("platform_label") or "")
    entries = priced + in_store
    best = priced[0] if priced else None

    return {
        "price_sources": entries,
        "landed_price_usd": best["landed_usd"] if best else None,
        "best_buy_url": best["url"] if best else None,
        "best_buy_platform": best["platform_label"] if best else None,
        "best_buy_shipping_usd": best["shipping_usd"] if best else 0,
        "best_buy_delivery": best["delivery_note"] if best else None,
    }