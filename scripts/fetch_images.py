#!/usr/bin/env python3
"""One-off: probe product pages for og:image URLs."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scrape import fetch_url
from src.images import extract_image_url

cache = ROOT / "data" / "raw"
probes = [
    ("xp-lite", "https://lectricebikes.com/products/xp-lite-arctic-white"),
    ("xp4", "https://lectricebikes.com/products/xp-black"),
    ("radmission2", "https://www.radpowerbikes.com/products/radmission-2"),
    ("radrunner3", "https://www.radpowerbikes.com/products/radrunner-3-plus"),
    ("batch", "https://www.batchbicycles.com/products/batch-e-bike"),
    ("super73-z", "https://super73.com/products/z1"),
    ("super73-zg", "https://super73.com/products/zg"),
    ("wallke-h7", "https://wallkebike.com/products/wallke-h7"),
    ("velotric-nomad", "https://www.velotricbike.com/products/velotric-nomad-1-plus-step-thru"),
    ("portola", "https://ride1up.com/product/portola/"),
    ("roadster", "https://ride1up.com/product/roadster-v3/"),
    ("zooz-ripster", "https://zoozbikes.com/products/ultra-ripster-gen-2"),
]

for name, url in probes:
    try:
        html = fetch_url(url, cache, delay=0.15)
        img = extract_image_url(html)
        print(f"{name}: {img}")
    except Exception as e:
        print(f"{name}: ERR {e}")