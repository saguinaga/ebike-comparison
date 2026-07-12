import json
import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

TIER_LABELS = {
    "budget": "$300–600",
    "value": "$600–1,200",
    "mid": "$1,200–2,000",
    "premium": "$2,000+",
    "baseline": "Baseline",
}


def load_reviewed(root: Path) -> list:
    reviewed = root / "data" / "bikes_reviewed.json"
    raw = root / "data" / "bikes.json"
    path = reviewed if reviewed.exists() else raw
    return json.loads(path.read_text(encoding="utf-8"))


def build(root: Path, min_bikes: int = 18) -> None:
    bikes = load_reviewed(root)
    e_bikes = [b for b in bikes if not b.get("is_baseline")]
    if len(e_bikes) < min_bikes:
        raise SystemExit(f"Need at least {min_bikes} e-bikes, found {len(e_bikes)}")

    bench = yaml.safe_load((root / "config" / "benchmarks.yaml").read_text(encoding="utf-8"))
    legal = json.loads((root / "data" / "legal_rules.json").read_text(encoding="utf-8"))
    safety = json.loads((root / "data" / "safety_research.json").read_text(encoding="utf-8"))

    baseline = next((b for b in bikes if b.get("is_baseline")), bench["baseline"])
    rider = bench.get("rider", {})
    main_site = bench.get("main_site_url", "#")

    by_tier = {}
    for b in e_bikes:
        tier = b.get("tier", "other")
        by_tier.setdefault(tier, []).append(b)

    env = Environment(loader=FileSystemLoader(root / "web" / "templates"), autoescape=True)
    template = env.get_template("index.html.j2")
    html = template.render(
        bikes=e_bikes,
        baseline=baseline,
        by_tier=by_tier,
        tier_labels=TIER_LABELS,
        rider=rider,
        legal=legal,
        safety=safety,
        main_site_url=main_site,
        generated_date="2026-07-12",
    )

    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(html, encoding="utf-8")

    for asset in ("styles.css", "app.js"):
        src = root / "web" / asset
        if src.exists():
            shutil.copy(src, docs / asset)