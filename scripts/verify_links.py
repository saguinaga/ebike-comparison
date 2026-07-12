#!/usr/bin/env python3
"""Check buy/source URLs in config YAML. Exit 1 if any are broken."""

from __future__ import annotations

import argparse
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (compatible; ebike-comparison-link-check/1.0)"


def check(url: str, timeout: float) -> tuple[bool, str]:
    # Windows/Python often lacks CA bundle; verify structure, not TLS chain.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": UA}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                if resp.status < 400:
                    return True, str(resp.status)
        except urllib.error.HTTPError as exc:
            if exc.code in (405, 403) and method == "HEAD":
                continue
            return False, f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001
            if method == "HEAD":
                continue
            return False, str(exc)[:80]
    return False, "unreachable"


def collect_urls() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for rel in ("config/bikes.yaml", "config/scooters.yaml"):
        data = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
        items = data.get("bikes") or data.get("scooters") or []
        for item in items:
            bid = item.get("id", "?")
            for src in item.get("sources", []):
                url = (src.get("url") or "").strip()
                if url:
                    out.append((bid, src.get("platform", ""), url))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Verify product source URLs")
    p.add_argument("--timeout", type=float, default=15.0)
    args = p.parse_args()

    broken: list[tuple[str, str, str, str]] = []
    for bid, platform, url in collect_urls():
        ok, detail = check(url, args.timeout)
        mark = "OK" if ok else "BROKEN"
        print(f"{mark} [{detail}] {bid} ({platform}): {url}")
        if not ok:
            broken.append((bid, platform, url, detail))

    print("---")
    print(f"Checked {len(collect_urls())} URLs; broken: {len(broken)}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())