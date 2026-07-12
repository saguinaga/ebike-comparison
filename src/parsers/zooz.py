import json
import re
from bs4 import BeautifulSoup


def parse_zooz(html: str, config: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {"field_confidence": {}}

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Product":
                    offers = item.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    price = offers.get("price")
                    if price:
                        result["price_usd"] = float(price)
                        result["field_confidence"]["price_usd"] = 0.85
                    if item.get("name"):
                        result["model"] = item["name"]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    text = soup.get_text(" ", strip=True)
    for pattern, field, conf in [
        (r"750\s*W", "motor_w", 0.7),
        (r"28\s*mph", "max_speed_mph", 0.7),
        (r"hydraulic", "brake_type", 0.6),
    ]:
        if re.search(pattern, text, re.I):
            if field == "brake_type":
                result[field] = "hydraulic_disc"
            elif field == "motor_w":
                result[field] = 750
            elif field == "max_speed_mph":
                result[field] = 28
            result["field_confidence"][field] = conf

    manual = config.get("manual", {})
    for k, v in manual.items():
        if v is not None:
            result[k] = v
            result["field_confidence"][k] = 0.9
    return result