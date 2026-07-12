def compare_to_baseline(bike: dict, baseline: dict) -> dict:
    b_price = baseline.get("price_usd") or 289
    e_price = bike.get("landed_price_usd") or bike.get("price_usd") or 0
    ratio = round(e_price / b_price, 1) if b_price else None

    b_speed = baseline.get("max_speed_mph") or 15
    e_speed = bike.get("max_speed_mph") or 20
    speed_delta = e_speed - b_speed

    brake_upgrade = bike.get("brake_type") not in ("coaster", "rim", None)

    b_weight = baseline.get("weight_lb")
    e_weight = bike.get("weight_lb")
    weight_delta = None
    if b_weight is not None and e_weight is not None:
        weight_delta = round(e_weight - b_weight, 1)

    return {
        "price_multiplier": ratio,
        "speed_delta_mph": speed_delta,
        "weight_delta_lb": weight_delta,
        "brake_upgrade": brake_upgrade,
        "baseline_model": baseline.get("model"),
        "baseline_price": b_price,
        "baseline_weight_lb": b_weight,
    }