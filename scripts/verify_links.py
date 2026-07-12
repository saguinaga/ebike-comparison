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


def _ssl_context() -> ssl.SSLContext:
    # Windows/Python often lacks a CA bundle; check reachability, not TLS chain.
    try:
        return ssl._create_unverified_context()
    except AttributeError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


def _is_transient_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(
        token in msg
        for token in (
            "certificate verify failed",
            "ssl",
            "timed out",
            "timeout",
            "temporary failure",
            "connection reset",
            "connection aborted",
            "eof occurred",
        )
    )


def check(url: str, timeout: float, retries: int = 2) -> tuple[bool, str]:
    ctx = _ssl_context()
    headers = {"User-Agent": UA}
    last_detail = "unreachable"

    for attempt in range(retries + 1):
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
                last_detail = str(exc)[:80]
                if method == "HEAD":
                    continue
                if _is_transient_error(exc) and attempt < retries:
                    break
                return False, last_detail
        else:
            return False, last_detail

    return False, last_detail


def _is_checkable_url(url: str) -> bool:
    lower = url.lower()
    if "/s?" in lower or "searchterm=" in lower:
        return False
    if "wholesale" in lower or "/w/" in lower:
        return False
    return True


def collect_urls() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for rel in ("config/bikes.yaml", "config/scooters.yaml"):
        data = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
        items = data.get("bikes") or data.get("scooters") or []
        for item in items:
            bid = item.get("id", "?")
            for src in item.get("sources", []):
                url = (src.get("url") or "").strip()
                if url and _is_checkable_url(url):
                    out.append((bid, src.get("platform", ""), url))

    retail_path = ROOT / "config" / "retail_sources.yaml"
    if retail_path.exists():
        retail = yaml.safe_load(retail_path.read_text(encoding="utf-8")) or {}
        retailers = retail.get("retailers", {})
        for bid, entries in (retail.get("products") or {}).items():
            for entry in entries:
                if entry.get("skip"):
                    continue
                url = (entry.get("url") or "").strip()
                if not url:
                    key = entry.get("retailer", "")
                    url = (retailers.get(key) or {}).get("url", "").strip()
                if url and _is_checkable_url(url):
                    out.append((bid, entry.get("retailer", "retail"), url))
        for kind, entries in (retail.get("defaults") or {}).items():
            for entry in entries:
                key = entry.get("retailer", "")
                url = (retailers.get(key) or {}).get("url", "").strip()
                if url and _is_checkable_url(url):
                    out.append((f"default:{kind}", key, url))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Verify product source URLs")
    p.add_argument("--timeout", type=float, default=15.0)
    args = p.parse_args()

    urls = collect_urls()
    broken: list[tuple[str, str, str, str]] = []
    for bid, platform, url in urls:
        ok, detail = check(url, args.timeout)
        mark = "OK" if ok else "BROKEN"
        print(f"{mark} [{detail}] {bid} ({platform}): {url}")
        if not ok:
            broken.append((bid, platform, url, detail))

    print("---")
    print(f"Checked {len(urls)} URLs; broken: {len(broken)}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())