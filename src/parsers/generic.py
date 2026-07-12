import json
import re

from bs4 import BeautifulSoup

from ..images import extract_image_url


def _parse_price(text: str) -> float | None:
    m = re.search(r"\$[\d,]+(?:\.\d{2})?", text or "")
    if not m:
        return None
    return float(m.group().replace("$", "").replace(",", ""))


def _extract_shopify_price(html: str) -> float | None:
    """Read current variant prices from Shopify meta.product (cents)."""
    m = re.search(r"var meta = (\{.*?\});\s*\n", html, re.S)
    if not m:
        return None
    try:
        meta = json.loads(m.group(1))
        variants = meta.get("product", {}).get("variants", [])
        cents = [v["price"] for v in variants if v.get("price")]
        if cents:
            return min(cents) / 100.0
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    return None


def _extract_jsonld_price(html: str) -> float | None:
    soup = BeautifulSoup(html, "html.parser")
    prices: list[float] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if item.get("@type") != "Product":
                continue
            offers = item.get("offers")
            if isinstance(offers, dict):
                offers = [offers]
            elif not isinstance(offers, list):
                continue
            for offer in offers:
                price = offer.get("price")
                if price is not None:
                    prices.append(float(price))
    return min(prices) if prices else None


def _extract_woocommerce_price(html: str) -> float | None:
    amounts = [
        float(m.group(1).replace(",", ""))
        for m in re.finditer(
            r'class="woocommerce-Price-amount amount"[^>]*>.*?>\$([\d,]+(?:\.\d{2})?)',
            html,
            re.S,
        )
    ]
    if amounts:
        return min(amounts)
    starting = re.search(
        r"starting at \$([\d,]+(?:\.\d{2})?)",
        html,
        re.I,
    )
    if starting:
        return float(starting.group(1).replace(",", ""))
    return None


def _extract_sale_price(html: str) -> tuple[float | None, float]:
    """Return (price, confidence). Structured sources rank above page text."""
    for extractor, confidence in (
        (_extract_shopify_price, 0.9),
        (_extract_jsonld_price, 0.88),
        (_extract_woocommerce_price, 0.88),
    ):
        price = extractor(html)
        if price:
            return price, confidence

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    sale = re.search(r"Sale price\s*\$[\d,]+(?:\.\d{2})?", text, re.I)
    if sale:
        return _parse_price(sale.group()), 0.7
    starting = re.search(
        r"(?:starting at|from)\s*\$[\d,]+(?:\.\d{2})?",
        text,
        re.I,
    )
    if starting:
        return _parse_price(starting.group()), 0.65
    loose = _parse_price(text)
    if loose:
        return loose, 0.35
    return None, 0.0


def parse_generic(html: str, config: dict) -> dict:
    price, price_confidence = _extract_sale_price(html)
    result = {"field_confidence": {}}
    if price:
        result["price_usd"] = price
        result["field_confidence"]["price_usd"] = price_confidence
    img = extract_image_url(html)
    if img:
        result["image_url"] = img
        result["field_confidence"]["image_url"] = 0.5

    manual = config.get("manual", {})
    for k, v in manual.items():
        if v is not None:
            result[k] = v
            result["field_confidence"][k] = 0.8 if k != "price_usd" else 0.9
    return result