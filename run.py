#!/usr/bin/env python3
"""E-bike comparison pipeline: scrape → review → build → publish."""

import argparse
import json
import shutil
from pathlib import Path

from src.build_site import build
from src.parse import parse_all, save_bikes

ROOT = Path(__file__).parent


def cmd_scrape(args):
    bikes = parse_all(ROOT, scrape_live=not args.offline)
    save_bikes(ROOT, bikes, "bikes.json")
    shutil.copy(ROOT / "data" / "bikes.json", ROOT / "data" / "bikes_reviewed.json")
    print(f"Scraped {len(bikes) - 1} e-bikes + baseline → data/bikes.json")


def cmd_build(args):
    build(ROOT, min_bikes=args.min_bikes)
    print(f"Built → docs/index.html ({args.min_bikes}+ e-bikes required)")


def cmd_deploy(args):
    src = ROOT / "docs"
    dest = Path(args.dest).expanduser().resolve()
    if not src.is_dir():
        raise SystemExit("Run `python run.py build` first.")
    shutil.copytree(src, dest, dirs_exist_ok=True)
    print(f"Deployed → {dest}")


def cmd_all(args):
    cmd_scrape(args)
    if not hasattr(args, "min_bikes"):
        args.min_bikes = 18
    cmd_build(args)


def main():
    p = argparse.ArgumentParser(description="E-bike comparison pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    for name in ("scrape", "all"):
        sp = sub.add_parser(name)
        sp.add_argument("--offline", action="store_true", help="Skip live HTTP fetches")
        sp.set_defaults(func=cmd_scrape if name == "scrape" else cmd_all)

    bp = sub.add_parser("build")
    bp.add_argument("--min-bikes", type=int, default=18)
    bp.set_defaults(func=cmd_build)

    dp = sub.add_parser("deploy", help="Copy docs/ to seanh2o live folder")
    dp.add_argument(
        "--dest",
        default=str(Path.home() / "seanh2o" / "ebike-comparison"),
        help="Live site folder (default: ~/seanh2o/ebike-comparison)",
    )
    dp.set_defaults(func=cmd_deploy)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()