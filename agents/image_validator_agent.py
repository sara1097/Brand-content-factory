"""
Image Validator Agent + product image acquisition.

Two responsibilities:

1. `validate_image_match` -- show one image to the Groq vision model and
   ask, strictly, whether it shows the product described by the user.

2. `acquire_product_image` -- the "image acquisition" pipeline node:
   - if the user uploaded a photo, use it as-is;
   - otherwise scrape web candidates (tools/image_scraper.py) and accept
     the first one the vision model confirms matches the description.

The accepted image becomes the reference image for product analysis,
WanGP video generation, and Magic Hour image generation.
"""
from __future__ import annotations

from config import IMAGE_MATCH_MIN_CONFIDENCE
from tools.groq_vision import call_groq_vision, encode_image, parse_json_response
from tools.image_scraper import scrape_candidate_images

VALIDATION_PROMPT = """
You are a strict product-image verifier and quality judge.

You are given a PRODUCT DESCRIPTION and an IMAGE. First decide whether
the image clearly shows that exact kind of product (same product type;
and same brand/model whenever the description names one). Then rate the
image as a candidate reference photo.

Match rules:
- Logos, packaging or visible text contradicting the description => no match.
- A different product category, an accessory, or a lifestyle scene where
  the product is not clearly visible => no match.

Quality rating (0.0-1.0): sharpness and resolution; free of noise,
blur, compression artifacts, watermarks, overlay text, borders or
collage layouts. A crisp studio shot scores high; a noisy screenshot
scores low.

product_only: true only if the product is the sole subject -- no
people, hands, cluttered scenes, or multiple unrelated items.

background: "white" if the backdrop is plain white/very light studio,
"black" if plain black/very dark studio, otherwise "other".

Return ONLY this JSON object:
{"match": true/false, "confidence": 0.0-1.0, "quality": 0.0-1.0,
 "product_only": true/false, "background": "white"|"black"|"other",
 "reason": "one short sentence"}
"""


def validate_image_match(
    description: str,
    image_path: str,
    model: str | None = None,
) -> dict:
    """
    Returns {"match": bool, "confidence": float, "quality": float,
    "product_only": bool, "background": str, "reason": str}
    (or {"error": ...} if the vision call itself failed).
    """
    try:
        image_b64 = encode_image(image_path)
    except Exception as exc:
        return {"error": str(exc)}

    prompt = f"{VALIDATION_PROMPT}\n\nPRODUCT DESCRIPTION:\n{description}"

    try:
        raw = call_groq_vision(
            prompt=prompt,
            image_b64=image_b64,
            model=model,
            max_completion_tokens=350,
        )
    except Exception as exc:
        return {"error": str(exc)}

    parsed = parse_json_response(raw)
    if "error" in parsed:
        return parsed

    def _unit_float(value) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    background = str(parsed.get("background", "other")).strip().lower()
    if background not in {"white", "black"}:
        background = "other"

    return {
        "match": bool(parsed.get("match")),
        "confidence": _unit_float(parsed.get("confidence", 0)),
        "quality": _unit_float(parsed.get("quality", 0)),
        "product_only": bool(parsed.get("product_only")),
        "background": background,
        "reason": str(parsed.get("reason", "")),
    }


def score_candidate(verdict: dict) -> float:
    """
    Composite score used to pick THE reference image among matching
    candidates: match confidence + image quality (no noise/watermarks),
    with bonuses for a product-only shot and a plain white/black studio
    background.
    """
    score = verdict.get("confidence", 0.0) + verdict.get("quality", 0.0)
    if verdict.get("product_only"):
        score += 0.5
    if verdict.get("background") in {"white", "black"}:
        score += 0.5
    return round(score, 3)


def acquire_product_image(
    description: str,
    uploaded_path: str | None = None,
    model: str | None = None,
    min_confidence: float = IMAGE_MATCH_MIN_CONFIDENCE,
    on_status=None,
) -> dict:
    """
    Resolve THE product reference image for this pipeline run.

    on_status, if given, is called with short human-readable progress
    strings (for the UI); it must never break acquisition.

    Returns:
        {
            "image_path": "outputs/scraped/candidate_2.jpg" | None,
            "source": "uploaded" | "scraped" | None,
            "query": "..."           # only for scraped
            "validation": {...},      # verdict for the accepted image
            "rejected": [{"path": ..., "reason": ...}, ...],
            "message": "...",
        }
    """

    def _status(text: str) -> None:
        print(f"[ImageAcquisition] {text}")
        if on_status is None:
            return
        try:
            on_status(text)
        except Exception:
            pass

    if uploaded_path:
        _status("Using the uploaded product photo.")
        return {
            "image_path": uploaded_path,
            "source": "uploaded",
            "rejected": [],
            "message": "User-uploaded image used as the product reference.",
        }

    _status("No photo uploaded — searching the web for a product image...")
    scrape = scrape_candidate_images(description)
    candidates = scrape["candidates"]

    if not candidates:
        return {
            "image_path": None,
            "source": None,
            "query": scrape["query"],
            "rejected": [],
            "message": "Web search returned no usable candidate images; "
                       "continuing without a reference image.",
        }

    # Score EVERY candidate, then pick the best -- not the first match.
    # The composite score prefers clean, sharp, watermark-free shots of
    # the product alone on a plain white/black background.
    evaluated: list[dict] = []
    rejected: list[dict] = []
    matches: list[dict] = []

    for i, candidate in enumerate(candidates, start=1):
        _status(f"Vision-scoring candidate {i}/{len(candidates)}...")
        verdict = validate_image_match(description, candidate, model=model)

        if verdict.get("error"):
            rejected.append({"path": candidate, "reason": verdict["error"]})
            continue

        entry = {"path": candidate, "score": score_candidate(verdict), **verdict}
        evaluated.append(entry)

        if verdict["match"] and verdict["confidence"] >= min_confidence:
            matches.append(entry)
        else:
            rejected.append({
                "path": candidate,
                "reason": verdict.get("reason") or f"low confidence {verdict['confidence']:.2f}",
            })

    if matches:
        best = max(matches, key=lambda entry: entry["score"])
        _status(
            f"Best candidate: {best['path']} (score {best['score']}, "
            f"quality {best['quality']:.2f}, background {best['background']}, "
            f"product_only {best['product_only']})"
        )
        return {
            "image_path": best["path"],
            "source": "scraped",
            "query": scrape["query"],
            "validation": best,
            "candidates_evaluated": evaluated,
            "rejected": rejected,
            "message": f"Best of {len(matches)} matching candidate(s) chosen "
                       f"by quality score ({best['score']}).",
        }

    return {
        "image_path": None,
        "source": None,
        "query": scrape["query"],
        "candidates_evaluated": evaluated,
        "rejected": rejected,
        "message": f"None of the {len(candidates)} scraped images matched the "
                   "description; continuing without a reference image.",
    }
