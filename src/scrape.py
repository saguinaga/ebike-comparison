import hashlib
import time
from pathlib import Path

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ebike-comparison/1.0; family research project)",
}


def fetch_url(url: str, cache_dir: Path, delay: float = 2.0) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(url.encode()).hexdigest()
    cache_file = cache_dir / f"{key}.html"

    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")

    time.sleep(delay)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text
    cache_file.write_text(html, encoding="utf-8")
    return html