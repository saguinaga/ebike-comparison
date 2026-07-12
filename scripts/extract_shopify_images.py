#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
imgs = re.findall(
    r"(https?://[^\"'\s]+/cdn/shop/files/[^\"'\s]+\.(?:jpg|jpeg|png|webp)[^\"'\s]*)",
    html,
    re.I,
)
seen = []
for u in imgs:
    if u not in seen:
        seen.append(u)
for u in seen[:12]:
    print(u)