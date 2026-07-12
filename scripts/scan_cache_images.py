#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.images import extract_image_url

for f in sorted((ROOT / "data" / "raw").glob("*.html")):
    html = f.read_text(encoding="utf-8", errors="replace")
    low = html.lower()
    if not any(k in low for k in ("radpower", "velotric", "batch", "wallke", "super73", "ride1up", "aventon", "zooz", "nakto", "heybike", "lectric")):
        continue
    img = extract_image_url(html)
    canon = re.search(r'rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html, re.I)
    title = re.search(r"<title>([^<]+)</title>", html, re.I)
    print(f.name[:10], (title.group(1)[:40] if title else "?"))
    print(" ", canon.group(1)[:70] if canon else "no-canonical")
    print(" ", img or "no-og")
    print()