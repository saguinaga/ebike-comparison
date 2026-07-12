# E-Bike Family Comparison

Interactive dashboard comparing ~20 solo-commute e-bikes for a 5'2" 12-year-old in Huntington Beach, CA 92646.

**Live site:** https://saguinaga.github.io/ebike-comparison/

## Quick start

```bash
cd C:\Users\seanr\OneDrive\Desktop\ebike-comparison
pip install -r requirements.txt
python run.py all
```

Open `docs/index.html` locally, or push to GitHub for Pages hosting.

## Commands

| Command | Description |
|---------|-------------|
| `python run.py scrape` | Fetch product pages, write `data/bikes.json` |
| `python run.py build` | Generate `docs/` for GitHub Pages |
| `python run.py all` | Scrape + build |
| `python run.py scrape --offline` | Use cached/manual data only |

## GitHub Pages

1. Push repo to `seanh2o/ebike-comparison`
2. Settings → Pages → Deploy from `/docs` folder
3. Family opens the published URL on a laptop

## Baseline bike

Firmstrong Urban Lady 26" Single Speed (Vanilla variant) — the bike your daughter rides today.