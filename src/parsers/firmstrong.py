import json
import re
from bs4 import BeautifulSoup

from ..images import extract_image_url


def parse_firmstrong(html: str, config: dict) -> dict:
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
                        result["field_confidence"]["price_usd"] = 0.9
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    text = soup.get_text(" ", strip=True)
    specs = {
        "weight_lb": r"(\d+\.?\d*)\s*lbs",
        "fit_height_min_in": r"5['\u2019]2",
        "tire_width_in": r"2\.125",
    }
    m = re.search(r"(\d+\.?\d*)\s*lbs", text, re.I)
    if m:
        result["weight_lb"] = float(m.group(1))
        result["field_confidence"]["weight_lb"] = 0.85

    img = extract_image_url(html)
    if img:
        result["image_url"] = img
        result["field_confidence"]["image_url"] = 0.85

    manual = config.get("manual", {})
    for k, v in (config.get("baseline", config)).items():
        if k not in ("url", "variant_id", "colors") and v is not None:
            result.setdefault(k, v)
    for k, v in manual.items():
        if v is not None:
            result[k] = v
    return result