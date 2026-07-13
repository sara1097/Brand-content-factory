"""
Web image scraping for the product reference image.

When the user runs the pipeline without uploading a product photo, this
module searches the web (DuckDuckGo image search, via the same `ddgs`
package already used by tools/web_search.py) for candidate product
images and downloads them locally. The vision validator
(agents/image_validator_agent.py) then decides which candidate actually
matches the product description before it is used as the reference
image for video (WanGP) and image (Magic Hour) generation.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

import requests
from ddgs import DDGS
from PIL import Image

from config import DEFAULT_MODEL, IMAGE_SCRAPE_MAX_CANDIDATES
from tools.groq_client import create_chat_completion, parse_json_response

# Downloaded candidates are re-encoded as JPEG so every downstream
# consumer (Groq vision, WanGP image_refs, Magic Hour upload) gets a
# predictable format regardless of what the web served (webp/avif/...).
MIN_IMAGE_DIMENSION = 200      # reject thumbnails/icons
MAX_IMAGE_DIMENSION = 2048     # cap huge originals
JPEG_QUALITY = 88
DOWNLOAD_TIMEOUT_SECONDS = 20

# Some hosts refuse requests without a browser-looking user agent.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def build_image_search_query(description: str) -> str:
    """
    Turn a (possibly long, possibly Arabic) product description into a
    short English image-search query. Uses a tiny Groq text call;
    falls back to the truncated description if that fails.
    """
    try:
        response = create_chat_completion(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You turn product descriptions into short web image "
                        'search queries. Return ONLY JSON: {"query": "..."}. '
                        "The query must be in English, at most 8 words, and "
                        "name the concrete product (brand + model + type)."
                    ),
                },
                {"role": "user", "content": description},
            ],
            temperature=0,
            max_completion_tokens=60,
            response_format={"type": "json_object"},
        )
        parsed = parse_json_response(response.choices[0].message.content)
        query = str(parsed.get("query", "")).strip()
        if query:
            return f"{query} product photo"
    except Exception as exc:
        print(f"[ImageScraper] Query extraction failed ({exc}); using raw description.")

    words = re.findall(r"\w+", description)[:8]
    return " ".join(words) + " product photo"


def search_image_urls(query: str, max_results: int = 15) -> list[str]:
    """Search DuckDuckGo Images and return full-size image URLs."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=max_results))
    except Exception as exc:
        print(f"[ImageScraper] Image search error for {query!r}: {exc}")
        return []
    return [r["image"] for r in results if r.get("image")]


def download_image(url: str, dest_path: Path) -> str | None:
    """
    Download one image URL, verify it decodes, normalize to JPEG, and
    save it. Returns the saved path or None if the candidate is unusable
    (dead link, not an image, too small, ...) -- never raises.
    """
    try:
        response = requests.get(url, headers=_HEADERS, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        if response.status_code != 200:
            return None

        with Image.open(io.BytesIO(response.content)) as image:
            if min(image.size) < MIN_IMAGE_DIMENSION:
                return None
            image = image.convert("RGB")
            image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(dest_path, format="JPEG", quality=JPEG_QUALITY)

        return str(dest_path)
    except Exception as exc:
        print(f"[ImageScraper] Skipping candidate {url[:80]}: {exc}")
        return None


def scrape_candidate_images(
    description: str,
    dest_dir: str = "outputs/scraped",
    max_candidates: int = IMAGE_SCRAPE_MAX_CANDIDATES,
) -> dict:
    """
    Search + download up to `max_candidates` usable candidate images for
    the described product.

    Returns:
        {"query": "...", "candidates": ["outputs/scraped/candidate_1.jpg", ...]}
    """
    query = build_image_search_query(description)
    print(f"[ImageScraper] Searching images for: {query!r}")

    # Fetch more URLs than needed; many image links are dead or tiny.
    urls = search_image_urls(query, max_results=max_candidates * 4)

    candidates: list[str] = []
    for url in urls:
        if len(candidates) >= max_candidates:
            break
        dest = Path(dest_dir) / f"candidate_{len(candidates) + 1}.jpg"
        saved = download_image(url, dest)
        if saved:
            candidates.append(saved)

    print(f"[ImageScraper] Downloaded {len(candidates)} usable candidate(s).")
    return {"query": query, "candidates": candidates}
