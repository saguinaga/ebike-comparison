"""Check Amazon /dp/ links in config for obvious dead listings."""
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scrape import HEADERS

DEAD_MARKERS = (
    "page not found",
    "dogs of amazon",
    "sorry! we couldn't find that page",
    "looking for something?",
    "we couldn't find that page",
    "cs_404_link",
    "gp/product/availability",
)

SEARCH_URL = re.compile(r"amazon\.com/s\?")


def collect_urls() -> dict[str, list[str]]:
    text = ""
    for rel in ("config/bikes.yaml", "config/scooters.yaml"):
        text += (ROOT / rel).read_text(encoding="utf-8")
    asin_urls = sorted(set(re.findall(r"https://www\.amazon\.com/dp/[A-Z0-9]{10}", text)))
    by_asin: dict[str, list[str]] = {}
    for url in asin_urls:
        asin = url.rsplit("/", 1)[-1]
        by_asin.setdefault(asin, []).append(url)
    return by_asin


def check_asin(asin: str) -> tuple[str, str]:
    url = f"https://www.amazon.com/dp/{asin}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
        body = resp.text.lower()
        title = ""
        m = re.search(r"<title>([^<]+)</title>", resp.text, re.I)
        if m:
            title = m.group(1).strip()
        if resp.status_code >= 400:
            return "dead", f"HTTP {resp.status_code} · {title}"
        if any(m in body for m in DEAD_MARKERS):
            return "dead", title or "404 page markers"
        if "add to cart" not in body and "add-to-cart" not in body and "producttitle" not in body:
            if "currently unavailable" in body:
                return "warn", title or "unavailable"
            return "warn", title or "no product signals"
        return "ok", title
    except Exception as exc:
        return "error", str(exc)


def main():
    extra = sys.argv[1:] if len(sys.argv) > 1 else []
    by_asin = collect_urls()
    for asin in extra:
        by_asin.setdefault(asin, [])
    dead = []
    for asin in sorted(by_asin):
        status, detail = check_asin(asin)
        print(f"{status.upper():5} {asin}  {detail[:100]}")
        if status == "dead":
            dead.append(asin)
    if dead:
        print("\nDEAD ASINs:", ", ".join(dead))
    else:
        print("\nNo dead ASINs detected.")


if __name__ == "__main__":
    main()