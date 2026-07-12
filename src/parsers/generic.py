import re
from bs4 import BeautifulSoup


def _parse_price(text: str) -> float | None:
    m = re.search(r"\$[\d,]+(?:\.\d{2})?", text or "")
    if not m:
        return None
    return float(m.group().replace("$", "").replace(",", ""))


def parse_generic(html: str, config: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    price = _parse_price(text)
    result = {"field_confidence": {}}
    if price:
        result["price_usd"] = price
        result["field_confidence"]["price_usd"] = 0.5
    manual = config.get("manual", {})
    for k, v in manual.items():
        if v is not None:
            result[k] = v
            result["field_confidence"][k] = 0.8 if k != "price_usd" else 0.9
    return result