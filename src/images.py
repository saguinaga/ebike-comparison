import hashlib
import json
import re
from pathlib import Path

import requests

from .scrape import HEADERS, fetch_url

MAX_GALLERY = 5


def extract_image_url(html: str) -> str | None:
    """Pull product image from og:image or JSON-LD Product."""
    m = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        html,
        re.I,
    )
    if m:
        url = m.group(1)
        if url.startswith("//"):
            return "https:" + url
        return url

    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    ):
        try:
            data = json.loads(block)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Product":
                    img = item.get("image")
                    if isinstance(img, list) and img:
                        return img[0]
                    if isinstance(img, str):
                        return img
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def download_image(url: str, dest: Path, timeout: int = 25) -> bool:
    if not url:
        return False
    if url.startswith("http://"):
        url = "https://" + url[7:]
    if url.startswith("//"):
        url = "https:" + url
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        return dest.stat().st_size > 400
    except Exception:
        return False


def local_image_path(bike_id: str, ext: str = "jpg") -> str:
    return f"images/{bike_id}.{ext}"


def _page_urls_for_bike(bike: dict) -> list[str]:
    urls = []
    if bike.get("url"):
        urls.append(bike["url"])
    for src in bike.get("sources", []):
        u = src.get("url")
        if u and "amazon.com/s?" not in u and "aliexpress" not in u:
            urls.append(u)
    for src in bike.get("sources", []):
        u = src.get("url")
        if u and u not in urls:
            urls.append(u)
    return urls


def image_source_urls(bike: dict) -> list[str]:
    urls = []
    primary = bike.get("image_url")
    if primary:
        urls.append(primary)
    for u in bike.get("image_urls") or []:
        if u and u not in urls:
            urls.append(u)
    return urls[:MAX_GALLERY]


def _manifest_path(docs_dir: Path, bike_id: str) -> Path:
    return docs_dir / "images" / f"{bike_id}.manifest"


def _gallery_filename(bike_id: str, index: int) -> str:
    return bike_id if index == 0 else f"{bike_id}-{index + 1}"


def _clear_bike_images(docs_dir: Path, bike_id: str) -> None:
    images_dir = docs_dir / "images"
    for path in images_dir.glob(f"{bike_id}*.jpg"):
        path.unlink(missing_ok=True)
    manifest = _manifest_path(docs_dir, bike_id)
    if manifest.exists():
        manifest.unlink()


def _scrape_primary_url(bike: dict, cache_dir: Path, fetch_live: bool) -> str | None:
    for page_url in _page_urls_for_bike(bike):
        html = None
        try:
            if fetch_live:
                html = fetch_url(page_url, cache_dir, delay=0.4)
            else:
                key = hashlib.md5(page_url.encode()).hexdigest()
                cache = cache_dir / f"{key}.html"
                if cache.exists():
                    html = cache.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if html:
            url = extract_image_url(html)
            if url:
                return url
    return None


def resolve_bike_images(
    bike: dict,
    root: Path,
    docs_dir: Path,
    cache_dir: Path,
    fetch_live: bool = True,
) -> dict:
    """Download primary + gallery images; return paths relative to docs/."""
    bike_id = bike.get("id", "unknown")
    sources = image_source_urls(bike)

    if not sources:
        scraped = _scrape_primary_url(bike, cache_dir, fetch_live)
        if scraped:
            sources = [scraped]

    manifest = _manifest_path(docs_dir, bike_id)
    sources_key = "\n".join(sources)
    stored_key = manifest.read_text(encoding="utf-8") if manifest.exists() else ""
    need_refresh = sources and (sources_key != stored_key)

    if need_refresh:
        _clear_bike_images(docs_dir, bike_id)

    gallery: list[str] = []
    for i, url in enumerate(sources):
        name = _gallery_filename(bike_id, i)
        dest = docs_dir / "images" / f"{name}.jpg"
        if need_refresh or not dest.exists() or dest.stat().st_size < 400:
            if not download_image(url, dest):
                continue
        if dest.exists() and dest.stat().st_size > 400:
            gallery.append(local_image_path(name))

    if not gallery and not sources:
        dest = docs_dir / "images" / f"{bike_id}.jpg"
        if dest.exists() and dest.stat().st_size > 400:
            gallery = [local_image_path(bike_id)]

    if gallery and sources:
        manifest.write_text(sources_key, encoding="utf-8")

    return {
        "image_src": gallery[0] if gallery else "",
        "image_gallery": gallery,
    }


def resolve_bike_image(
    bike: dict,
    root: Path,
    docs_dir: Path,
    cache_dir: Path,
    fetch_live: bool = True,
) -> str:
    return resolve_bike_images(bike, root, docs_dir, cache_dir, fetch_live)["image_src"]