# E-Bike Family Comparison

Interactive dashboard comparing ~20 solo-commute e-bikes for a 5'2" 12-year-old in Huntington Beach, CA 92646.

**Live site:** https://saguinaga.github.io/ebike-comparison/

## Quick start

```bash
cd C:\Users\seanr\OneDrive\Desktop\ebike-comparison
pip install -r requirements.txt
python run.py all
```

Open `docs/index.html` locally in your browser (double-click or `python -m http.server` from project root).

### Product images (3 options)

1. **Auto-scrape** — `python run.py scrape` pulls `og:image` from manufacturer pages; `python run.py build` saves to `docs/images/{bike-id}.jpg` for offline viewing.
2. **Manual URL** — add `image_url: https://...` under `manual:` in `config/bikes.yaml` for any bike (Amazon, AliExpress, etc.).
3. **Local file** — drop `docs/images/{bike-id}.jpg` yourself; rebuild picks it up.

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