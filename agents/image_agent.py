"""
Image generation agent (Magic Hour).

Flow:
  1. Take the content calendar's image days (media_type == "image" --
     4 days in the default 2 video / 4 image / 1 text weekly mix).
  2. Ask Qwen for ONE tailored image-generation prompt per image day,
     grounded in that day's post (post_idea / hook / visual_notes /
     platform) and the product's branding facts.
  3. Upload the product reference image to Magic Hour once (when
     available), then render each day's image via the AI Image Editor
     (reference + prompt) or the plain AI Image Generator (no reference).

Mirrors agents/video_agent.py: one self-contained entry point that
returns {"error": ...} instead of raising, so a failure never kills the
pipeline run.
"""
from __future__ import annotations

import json

from agents.content_calendar import days_by_media_type
from config import QWEN_MODEL
from models.llm import ask_qwen
from tools.magichour_client import (
    MagicHourClientError,
    generate_image,
    upload_reference_image,
)
from utils.json_parser import parse_json_response


def _fallback_prompt(day: dict, description: str) -> str:
    """Deterministic prompt used when Qwen's JSON didn't cover this day."""
    pieces = [
        day.get("post_idea") or description,
        day.get("visual_notes") or "",
        "Professional commercial product photograph, clean studio lighting, "
        "advertisement quality, sharp focus on the product. Only the product "
        "in frame: absolutely no text, titles, numbers, charts, badges, "
        "borders, logos or watermarks of any kind -- the only text allowed "
        "is what is physically printed on the real product itself, in "
        "English.",
    ]
    return " ".join(p.strip() for p in pieces if p and p.strip())


def _product_appearance(description: str, product: dict | None) -> str:
    """
    Compact, concrete description of what the product looks like.
    Appended to prompts that run WITHOUT the reference image, so the
    generated product matches the entered product as closely as possible.
    """
    product = product or {}

    facts = []
    for key in ("product_name", "brand", "category", "colors",
                "materials", "visible_text", "visible_logos"):
        value = product.get(key)
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value if v)
        if value:
            facts.append(f"{key.replace('_', ' ')}: {value}")

    desc = " ".join(description.split())
    if len(desc) > 350:
        desc = desc[:347] + "..."

    parts = [f"Depict this exact product, faithful to this description: {desc}."]
    if facts:
        parts.append("Known appearance -- " + "; ".join(facts) + ".")
    parts.append(
        "Photorealistic and accurate to the description; do not invent a "
        "different product design. Only the product in frame: absolutely "
        "no text, titles, numbers, charts, badges, borders, logos or "
        "watermarks of any kind -- the only text allowed is what is "
        "physically printed on the real product itself, in English."
    )
    return " ".join(parts)


def generate_image_prompts(
    description: str,
    days: list[dict],
    product: dict | None = None,
    marketing: dict | None = None,
    model: str | None = None,
) -> list[str]:
    """
    One image-generation prompt per calendar day, in day order. Never
    returns fewer prompts than days -- gaps are filled deterministically
    from the day's own post_idea/visual_notes.
    """
    product = product or {}

    branding_facts = {
        "product_name": product.get("product_name"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "colors": product.get("colors"),
        "visible_text": product.get("visible_text"),
        "visible_logos": product.get("visible_logos"),
    }

    day_briefs = [
        {
            "day": day.get("day"),
            "platform": day.get("platform"),
            "post_idea": day.get("post_idea"),
            "hook": day.get("hook"),
            "visual_notes": day.get("visual_notes"),
        }
        for day in days
    ]

    instruction = f"""
You are an expert prompt engineer for an AI image generator that edits a
real reference photo of the product.

Write ONE detailed image-generation prompt per calendar day below --
each prompt is a DIFFERENT static advertisement visual for the SAME
product, matching that day's post idea and visual notes.

Rules for EACH prompt:
- Write the prompt in ENGLISH, regardless of the language of the
  product description.
- Describe a single still image: setting/surface, lighting, mood, camera
  angle, and how the product is presented.
- Describe the product itself CONCRETELY in every prompt (exact product
  type, colors, materials, branding and visible text/logos from the
  facts and description below), so the image is still correct even if
  the reference photo cannot be used.
- The product is the HERO of a clean, photorealistic photograph --
  always in frame, unchanged and dominant. Realistic USAGE EXTERNALS
  are encouraged when they fit the day's idea: for packaged food, a
  prepared serving made with the product beside the pack (e.g. a fresh
  sandwich with the cheese visible next to the cheese pack); for
  drinks, a filled glass beside the bottle; for electronics, the
  device shown working (a TV displaying a vivid scene, a fridge open
  and stocked with fresh food); for cosmetics, a subtle texture swatch
  beside the bottle. Externals support the product -- they never
  replace it or hide it.
- Absolutely NO text of any kind anywhere in the image -- no titles,
  headlines, captions, slogans, prices, badges, labels, numbers,
  charts, graphs, arrows, diagrams, infographic elements, collage
  layouts, borders, frames, floating logos or watermarks. The only text
  that may exist is what is physically printed on the real product
  itself (English only, exactly as it really is -- never invented).
  State this explicitly in every prompt.
- If the day's post idea or visual notes call for text, statistics,
  charts, comparisons or collages, IGNORE those parts -- translate the
  idea into a purely visual product scene instead (setting, props,
  lighting, mood). Even for "infographic" or "carousel" days, the
  generated image must STILL be a pure product photo; any text/layout
  is added later by a designer, not inside this image.
- Commercial / social-media advertisement style, suited to the day's platform.
- 2 to 4 sentences, plain prose, no markdown.

Return ONLY this JSON object, nothing else:
{{"image_prompts": [{{"day": <day number>, "prompt": "<prompt>"}}]}}

User's product description:
{description}

Known product facts (ignore empty ones):
{json.dumps(branding_facts, indent=2, ensure_ascii=False)}

Calendar days to cover:
{json.dumps(day_briefs, indent=2, ensure_ascii=False)}

Marketing context (may be empty):
{json.dumps((marketing or {}).get("marketing_angles", []), ensure_ascii=False)}
"""

    prompts_by_day: dict = {}
    try:
        # 4 image prompts ~600 tokens; keep the completion reservation
        # small so prompt + reservation stays under Groq's 6000 TPM cap.
        parsed = parse_json_response(
            ask_qwen(instruction, model=model, max_completion_tokens=1500)
        )
        for item in parsed.get("image_prompts", []) if isinstance(parsed, dict) else []:
            prompt = str(item.get("prompt", "")).strip()
            if prompt:
                prompts_by_day[item.get("day")] = prompt
    except Exception as exc:
        print(f"[ImageAgent] Prompt generation failed ({exc}); using fallback prompts.")

    return [
        prompts_by_day.get(day.get("day")) or _fallback_prompt(day, description)
        for day in days
    ]


def generate_image_assets(
    description: str,
    product: dict | None = None,
    marketing: dict | None = None,
    content: dict | None = None,
    image_path: str | None = None,
    on_progress=None,
) -> dict:
    """
    Render one Magic Hour image for every image day in the calendar.

    Args mirror agents/video_agent.generate_video_assets; `image_path`
    is the product reference image (uploaded or scraped+validated).
    on_progress(index, total, status_text) drives the UI progress bar
    and must never break generation.

    Returns:
        {
            "num_images": 4,
            "reference_used": True,
            "images": [
                {"day": 2, "prompt": "...", "status": "succeeded",
                 "image_path": "outputs/images/<id>.png", ...},
                ...
            ],
        }
    or {"error": "..."} when nothing could be generated at all.
    """
    if not content or not isinstance(content, dict):
        return {"error": "No content calendar available -- image days unknown."}

    image_days = days_by_media_type(content, "image")
    if not image_days:
        return {"error": "The content calendar has no image days."}

    def _notify(index: int, total: int, status_text: str) -> None:
        if on_progress is None:
            return
        try:
            on_progress(index, total, status_text)
        except Exception:
            pass

    total = len(image_days)
    _notify(0, total, "Writing image prompts with Qwen...")

    prompts = generate_image_prompts(
        description=description,
        days=image_days,
        product=product,
        marketing=marketing,
        model=QWEN_MODEL,
    )

    reference_file_path = None
    if image_path:
        try:
            _notify(0, total, "Uploading product reference image to Magic Hour...")
            reference_file_path = upload_reference_image(image_path)
        except MagicHourClientError as exc:
            # Degrade to text-only generation rather than failing the node.
            print(f"[ImageAgent] Reference upload failed ({exc}); generating without it.")

    # When a prompt runs WITHOUT the reference photo (no reference at
    # all, or the editor endpoint rejected the submission), it gets this
    # concrete appearance description appended so the generated product
    # still matches the entered product as closely as possible.
    appearance = _product_appearance(description, product)

    images = []
    for i, (day, prompt) in enumerate(zip(image_days, prompts), start=1):
        day_number = day.get("day")
        _notify(i - 1, total, f"Rendering image {i}/{total} (day {day_number})...")

        enriched_prompt = f"{prompt} {appearance}"
        result = generate_image(
            prompt=prompt if reference_file_path else enriched_prompt,
            reference_file_path=reference_file_path,
            fallback_prompt=enriched_prompt,
            name=f"Day {day_number} - {day.get('post_idea', 'post')[:60]}",
        )
        images.append({"day": day_number, **result})
        _notify(i, total, f"Image {i}/{total} {result['status']}.")

    if all(img["status"] != "succeeded" for img in images):
        first_error = images[0].get("error", "unknown error")
        return {"error": f"All image generations failed. First error: {first_error}"}

    return {
        "num_images": len(images),
        "reference_used": bool(reference_file_path),
        "images": images,
    }
