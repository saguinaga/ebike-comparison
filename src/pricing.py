def compute_landed_prices(bike: dict) -> dict:
    manual = bike.get("manual", {})
    base_price = bike.get("price_usd") or manual.get("price_usd")
    shipping = manual.get("shipping_estimate_usd", 0)

    sources = []
    for src in bike.get("sources", []):
        platform = src.get("platform", "unknown")
        price = base_price
        ship = shipping if platform == "aliexpress" else 0
        if platform == "amazon":
            ship = 0  # often Prime
        landed = (price or 0) + (ship or 0)
        sources.append({
            "platform": platform,
            "url": src.get("url"),
            "item_price_usd": price,
            "shipping_usd": ship,
            "landed_usd": landed,
            "delivery_note": {
                "amazon": "Prime ~1-3 days",
                "aliexpress": "2-4 weeks",
                "manufacturer": "Direct ship",
            }.get(platform, "Varies"),
            "rewards_note": "Amazon 5% category cards may apply" if platform == "amazon" else None,
        })

    if not sources and base_price:
        sources.append({
            "platform": "manual",
            "landed_usd": base_price + shipping,
            "item_price_usd": base_price,
            "shipping_usd": shipping,
        })

    landed_values = [s["landed_usd"] for s in sources if s.get("landed_usd")]
    lowest = min(landed_values) if landed_values else base_price

    return {
        "price_sources": sources,
        "landed_price_usd": lowest,
    }