"""Web research helpers that return traceable, structured evidence."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from ddgs import DDGS


TRUSTED_EGYPTIAN_STORES = {
    "amazon.eg": 0.95,
    "noon.com": 0.90,
    "jumia.com.eg": 0.90,
    "btech.com": 0.90,
    "2b.com.eg": 0.85,
    "dream2000.com": 0.85,
    "tradeline.com": 0.85,
}

PRICE_PATTERNS = (
    re.compile(r"(?:EGP|LE|L\.E\.?|\u062c\u0646\u064a\u0647(?: \u0645\u0635\u0631\u064a)?)\s*([\d,.]+)", re.IGNORECASE),
    re.compile(r"([\d,.]+)\s*(?:EGP|LE|L\.E\.?|\u062c\u0646\u064a\u0647(?: \u0645\u0635\u0631\u064a)?)", re.IGNORECASE),
)


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _extract_price(text: str) -> float | None:
    for pattern in PRICE_PATTERNS:
        match = pattern.search(text or "")
        if not match:
            continue
        try:
            value = float(match.group(1).replace(",", ""))
            if 10 <= value <= 10_000_000:
                return value
        except ValueError:
            pass
    return None


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web and return normalized DuckDuckGo results."""
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results, region="eg-en"))
    except Exception as exc:
        print(f"Web search error for {query!r}: {exc}")
        return []


def _normalize_result(result: dict, kind: str) -> dict:
    url = result.get("href", "")
    domain = _domain(url)
    text = f"{result.get('title', '')} {result.get('body', '')}"
    price = _extract_price(text)
    base_confidence = TRUSTED_EGYPTIAN_STORES.get(domain, 0.55)
    confidence = min(0.99, base_confidence + (0.04 if price is not None else 0))
    return {
        "kind": kind,
        "title": result.get("title", "Untitled result"),
        "url": url,
        "domain": domain or "unknown",
        "snippet": result.get("body", "")[:350],
        "price_egp": price,
        "confidence": round(confidence, 2),
    }


def collect_market_evidence(product_name: str, category: str) -> dict:
    """Collect price and competitor evidence with URLs and confidence scores."""
    current_year = datetime.now().year
    price_queries = [
        f'"{product_name}" price Egypt EGP {current_year}',
        f'"{product_name}" Egypt local price',
        f'"{product_name}" (site:amazon.eg OR site:noon.com OR site:jumia.com.eg)',
    ]
    competitor_queries = [
        f"best {category} Egypt {current_year}",
        f"{category} alternatives Egypt prices",
    ]

    evidence: list[dict] = []
    for query in price_queries:
        evidence.extend(_normalize_result(item, "price") for item in search_web(query, 4))
    for query in competitor_queries:
        evidence.extend(_normalize_result(item, "competitor") for item in search_web(query, 4))

    unique: dict[str, dict] = {}
    for item in evidence:
        key = item["url"] or f'{item["kind"]}:{item["title"]}'
        if key not in unique:
            unique[key] = item

    items = list(unique.values())
    return {
        "searched_at": datetime.now(timezone.utc).isoformat(),
        "price_sources": [item for item in items if item["kind"] == "price"][:10],
        "competitor_sources": [item for item in items if item["kind"] == "competitor"][:8],
    }


def search_egyptian_prices(product_name: str) -> str:
    """Backward-compatible formatted price search."""
    evidence = collect_market_evidence(product_name, product_name)
    return "\n".join(
        f'- {item["title"]} | {item["price_egp"] or "price not shown"} | {item["url"]}'
        for item in evidence["price_sources"]
    ) or "No reliable prices were found."


def search_competitors(product_category: str) -> str:
    """Backward-compatible formatted competitor search."""
    evidence = collect_market_evidence(product_category, product_category)
    return "\n".join(
        f'- {item["title"]} | {item["url"]}'
        for item in evidence["competitor_sources"]
    ) or "No competitors were found."
