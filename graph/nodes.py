"""
LangGraph node functions.

Each node wraps one existing agent, preserving the fault-tolerant
contract of the old hand-written runner: on failure the node stores
{"node_error": ..., "message": ...} under its state key instead of
raising, and downstream nodes receive {} for errored inputs.

UI callbacks (progress bars, status lines) travel through
config["configurable"] -- they are optional and must never break a run:

    on_acquire_status(text)
    on_video_progress(variant, total, pct, status, phase)
    on_image_progress(index, total, text)
"""
from __future__ import annotations

import json
from typing import Callable

from langchain_core.runnables import RunnableConfig

from agents.compliance_agent import generate_compliance
from agents.content_agent import generate_content
from agents.image_agent import generate_image_assets
from agents.image_validator_agent import acquire_product_image
from agents.marketing_strategy_agent import build_marketing_strategy
from agents.product_agent import analyze_product
from agents.report_agent import generate_report
from agents.research_agent import research_market
from agents.variant_agent import extract_hooks_and_ctas, generate_variants
from agents.video_agent import generate_video_assets
from config import ENABLE_VIDEO_GENERATION, PRODUCT_MODEL
from graph.state import PipelineState

# ============================================================
# MODELS + TPM-SAFE TOKEN BUDGETS (moved here from app_qwen.py so the
# graph is runnable without Streamlit; tuned to Groq's ~6000 TPM limit)
# ============================================================
VISION_MODEL = PRODUCT_MODEL
QWEN_TEXT_MODEL = "qwen/qwen3-32b"

VISION_MAX_TOKENS = 700
RESEARCH_SETTINGS = {"num_predict": 1500}
RESEARCH_MAX_PRICE_SOURCES = 5
RESEARCH_MAX_COMPETITOR_SOURCES = 3
MARKETING_SETTINGS = {"num_predict": 900}
CONTENT_MAX_TOKENS = 2000
VARIANT_SETTINGS = {"num_predict": 1200}
COMPLIANCE_SETTINGS = {"num_predict": 1200}
REPORT_SETTINGS = {"num_predict": 1200}
REPORT_SECTION_MAX_CHARS = 300


# ============================================================
# HELPERS
# ============================================================

def _cfg(config: RunnableConfig | None, key: str) -> Callable | None:
    """Optional UI callback from config['configurable']."""
    return ((config or {}).get("configurable") or {}).get(key)


def _ok(data) -> dict:
    """Usable upstream data, or {} if that node errored / never ran."""
    if isinstance(data, dict) and "node_error" not in data:
        return data
    return {}


def _run_node(key: str, failure_message: str, fn: Callable[[], dict]) -> dict:
    """Uniform fault-tolerant node body."""
    try:
        result = fn()
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(result["error"])
        return {key: result}
    except Exception as exc:
        return {key: {"node_error": str(exc), "message": failure_message}}


def _condense_for_report(data: dict | None, max_chars: int = REPORT_SECTION_MAX_CHARS) -> dict:
    if not data:
        return {}
    condensed = {}
    for key, value in data.items():
        if key in {"data_sources", "metadata", "evidence", "strategy_score"}:
            continue
        text = json.dumps(value, ensure_ascii=False)
        condensed[key] = value if len(text) <= max_chars else text[:max_chars] + "...(truncated)"
    return condensed


# ============================================================
# NODES
# ============================================================

def acquire_image_node(state: PipelineState, config: RunnableConfig) -> dict:
    """Resolve the product reference image: uploaded photo as-is, else
    web-scrape candidates and keep the first one the vision model
    confirms matches the description. Never blocks the pipeline -- with
    no usable image the run simply continues without a reference."""
    try:
        acquisition = acquire_product_image(
            description=state["description"],
            uploaded_path=state.get("uploaded_image_path"),
            on_status=_cfg(config, "on_acquire_status"),
        )
    except Exception as exc:
        return {
            "image_acquisition": {
                "node_error": str(exc),
                "message": "Product image acquisition failed.",
            },
            "image_path": state.get("uploaded_image_path"),
        }
    return {
        "image_acquisition": acquisition,
        "image_path": acquisition.get("image_path"),
    }


def product_node(state: PipelineState, config: RunnableConfig) -> dict:
    return _run_node("product", "Failed to analyze product.", lambda: analyze_product(
        text_description=state["description"],
        image_path=state.get("image_path"),
        model=VISION_MODEL,
        max_completion_tokens=VISION_MAX_TOKENS,
    ))


def research_node(state: PipelineState, config: RunnableConfig) -> dict:
    return _run_node("research", "Market research failed.", lambda: research_market(
        _ok(state.get("product")),
        model=QWEN_TEXT_MODEL,
        settings_overrides=RESEARCH_SETTINGS,
        max_price_sources=RESEARCH_MAX_PRICE_SOURCES,
        max_competitor_sources=RESEARCH_MAX_COMPETITOR_SOURCES,
    ))


def marketing_node(state: PipelineState, config: RunnableConfig) -> dict:
    return _run_node("marketing", "Marketing strategy generation failed.", lambda: build_marketing_strategy(
        product_intelligence=_ok(state.get("product")),
        market_intelligence=_ok(state.get("research")),
        business_constraints=state.get("business_constraints") or {},
        model=QWEN_TEXT_MODEL,
        settings_overrides=MARKETING_SETTINGS,
    ))


def content_node(state: PipelineState, config: RunnableConfig) -> dict:
    return _run_node("content", "Content calendar generation failed.", lambda: generate_content(
        _ok(state.get("marketing")),
        model=QWEN_TEXT_MODEL,
        max_completion_tokens=CONTENT_MAX_TOKENS,
    ))


def variants_node(state: PipelineState, config: RunnableConfig) -> dict:
    """A/B/C ad variants for EVERY calendar day (Lojain's per-day flow):
    each day's call receives the hooks/CTAs of all previous days as
    anti-repetition memory, so no two days reuse an opener or CTA."""

    def _run() -> dict:
        marketing = _ok(state.get("marketing"))
        days = _ok(state.get("content")).get("days") or []

        if not days:
            # No calendar available -- single-shot generation (old behavior).
            return generate_variants(
                marketing, None,
                model=QWEN_TEXT_MODEL, settings_overrides=VARIANT_SETTINGS,
            )

        used_hooks: list[str] = []
        used_ctas: list[str] = []
        day_entries: list[dict] = []
        failures = 0

        for day in days:
            day_variants = generate_variants(
                marketing,
                {"days": [day]},
                model=QWEN_TEXT_MODEL,
                settings_overrides=VARIANT_SETTINGS,
                previous_hooks=used_hooks,
                previous_ctas=used_ctas,
            )

            entry = {
                "day": day.get("day"),
                "platform": day.get("platform"),
                "topic": day.get("post_idea"),
            }

            if isinstance(day_variants, dict) and "error" in day_variants:
                failures += 1
                entry["error"] = day_variants["error"]
            else:
                new_hooks, new_ctas = extract_hooks_and_ctas(day_variants)
                used_hooks.extend(new_hooks)
                used_ctas.extend(new_ctas)
                entry["variants"] = day_variants

            day_entries.append(entry)

        if failures == len(days):
            raise RuntimeError(
                f"Variant generation failed for all {len(days)} days. "
                f"First error: {day_entries[0].get('error')}"
            )

        return {
            "days": day_entries,
            "metadata": {"agent": "variant", "status": "success"},
        }

    return _run_node("variants", "Marketing variant generation failed.", _run)


def compliance_node(state: PipelineState, config: RunnableConfig) -> dict:
    """Compliance review matching the per-day variants: every day's
    A/B/C set gets its own review call, so all 7 days of ad copy are
    covered (not just a representative sample). Single-shot variant
    results (no calendar) keep the old one-call behavior."""

    def _run() -> dict:
        marketing = _ok(state.get("marketing"))
        variants = _ok(state.get("variants"))

        if "days" not in variants:
            return generate_compliance(
                marketing, variants,
                model=QWEN_TEXT_MODEL, settings_overrides=COMPLIANCE_SETTINGS,
            )

        day_entries: list[dict] = []
        successes = 0

        for entry in variants.get("days", []):
            day_result = {
                "day": entry.get("day"),
                "platform": entry.get("platform"),
                "topic": entry.get("topic"),
            }

            if not entry.get("variants"):
                day_result["error"] = entry.get("error", "No variants were generated for this day.")
                day_entries.append(day_result)
                continue

            review = generate_compliance(
                marketing, entry["variants"],
                model=QWEN_TEXT_MODEL, settings_overrides=COMPLIANCE_SETTINGS,
            )

            if isinstance(review, dict) and "error" in review:
                day_result["error"] = review["error"]
            else:
                day_result["compliance"] = review
                successes += 1
            day_entries.append(day_result)

        if not successes:
            first_error = next((d.get("error") for d in day_entries if d.get("error")), "unknown")
            raise RuntimeError(
                f"Compliance review failed for all {len(day_entries)} days. "
                f"First error: {first_error}"
            )

        return {
            "days": day_entries,
            "metadata": {"agent": "compliance", "status": "success",
                         "reviewed_days": successes},
        }

    return _run_node("compliance", "Compliance review failed.", _run)


def video_node(state: PipelineState, config: RunnableConfig) -> dict:
    """2 WanGP videos for the calendar's 2 video days (parallel branch)."""
    if not state.get("enable_video", ENABLE_VIDEO_GENERATION):
        return {"video": {
            "skipped": True,
            "message": "Video generation disabled for this run (sidebar toggle / "
                       "ENABLE_VIDEO_GENERATION in .env). Video days keep their "
                       "text content; no videos were rendered.",
            "variants": [],
        }}
    return _run_node("video", "Video generation failed.", lambda: generate_video_assets(
        description=state["description"],
        product=_ok(state.get("product")),
        marketing=_ok(state.get("marketing")),
        content=_ok(state.get("content")),
        image_path=state.get("image_path"),
        on_progress=_cfg(config, "on_video_progress"),
    ))


def images_node(state: PipelineState, config: RunnableConfig) -> dict:
    """4 Magic Hour images for the calendar's 4 image days (parallel branch)."""
    return _run_node("images", "Post image generation failed.", lambda: generate_image_assets(
        description=state["description"],
        product=_ok(state.get("product")),
        marketing=_ok(state.get("marketing")),
        content=_ok(state.get("content")),
        image_path=state.get("image_path"),
        on_progress=_cfg(config, "on_image_progress"),
    ))


def _ad_captions_by_day(state: PipelineState) -> dict:
    """Per-day 'extra caption' for the final plan: the compliance-safe
    variant A when its review succeeded, else the raw variant A. Keys
    are day numbers; values are {hook, body, cta, source}."""
    result: dict = {}

    for entry in _ok(state.get("variants")).get("days", []):
        variant_a = (entry.get("variants") or {}).get("variant_a") or {}
        if any(variant_a.get(k) for k in ("hook", "body", "cta")):
            result[entry.get("day")] = {**variant_a, "source": "variant"}

    for entry in _ok(state.get("compliance")).get("days", []):
        review = entry.get("compliance") or {}
        safe = (review.get("variant_a") or {}).get("safe_campaign_text") or {}
        if any(safe.get(k) for k in ("hook", "body", "cta")):
            result[entry.get("day")] = {**safe, "source": "compliance_safe"}

    return result


def assemble_calendar_node(state: PipelineState, config: RunnableConfig) -> dict:
    """Join node: attach each rendered video/image to its calendar day,
    producing the final deliverable -- 7 posts where 2 carry a video,
    4 carry an image and 1 is text-only. Each day also carries an
    'extra_caption': that day's compliance-safe ad variant (the ad
    option), so the calendar caption and ad copy sit side by side."""
    content = _ok(state.get("content"))
    if not content.get("days"):
        return {"final_calendar": {
            "node_error": "No content calendar available.",
            "message": "Cannot assemble the 7-day plan without a calendar.",
        }}

    video = _ok(state.get("video"))
    images = _ok(state.get("images"))
    ad_captions = _ad_captions_by_day(state)

    videos_by_day = {
        v["day"]: v for v in video.get("variants", []) if v.get("day") is not None
    }
    images_by_day = {
        img["day"]: img for img in images.get("images", []) if img.get("day") is not None
    }

    final_days = []
    mix_counts: dict[str, int] = {}
    for day in content["days"]:
        entry = dict(day)
        if ad_captions.get(entry.get("day")):
            entry["extra_caption"] = ad_captions[entry.get("day")]
        media_type = entry.get("media_type") or "text"
        mix_counts[media_type] = mix_counts.get(media_type, 0) + 1

        if media_type == "video":
            if video.get("skipped"):
                entry["media_status"] = "skipped"
                entry["media_path"] = None
                final_days.append(entry)
                continue
            asset = videos_by_day.get(entry.get("day"))
            path_key = "video_path"
        elif media_type == "image":
            asset = images_by_day.get(entry.get("day"))
            path_key = "image_path"
        else:
            entry["media_status"] = "not_required"
            entry["media_path"] = None
            final_days.append(entry)
            continue

        if asset is None:
            entry["media_status"] = "missing"
            entry["media_path"] = None
        else:
            entry["media_status"] = asset.get("status")
            entry["media_path"] = asset.get(path_key)
            entry["media_prompt"] = asset.get("prompt")
            if "reference_used" in asset:
                entry["media_reference_used"] = asset["reference_used"]
            if asset.get("error"):
                entry["media_error"] = asset["error"]
        final_days.append(entry)

    return {"final_calendar": {
        "campaign_name": content.get("campaign_name"),
        "media_mix": mix_counts,
        "days": final_days,
    }}


def report_node(state: PipelineState, config: RunnableConfig) -> dict:
    return _run_node("report", "Executive report generation failed.", lambda: generate_report(
        product_intelligence=_condense_for_report(state.get("product")),
        market_intelligence=_condense_for_report(state.get("research")),
        marketing_strategy=_condense_for_report(state.get("marketing")),
        variants=_condense_for_report(state.get("variants")),
        compliance=_condense_for_report(state.get("compliance")),
        content=_condense_for_report(state.get("content")),
        model=QWEN_TEXT_MODEL,
        settings_overrides=REPORT_SETTINGS,
    ))
