"""
Variant Agent

Generates A/B/C marketing ad variants
from Marketing Strategy.
"""

from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.prompts.constants import AGENT_SETTINGS
from core.validator import validate_output

from agents.prompts.variant_prompt import (
    VARIANT_SYSTEM_PROMPT,
    VARIANT_TASK_PROMPT,
    BANNED_OPENERS,
    BANNED_CTA_PATTERNS,
    BANNED_WORDS_OVERUSED,
    format_used_list,
)

# ============================================================
# BUILD VARIANT INPUT
# ============================================================

def _summarize_content_calendar(content: dict | None) -> str:
    """Condense the content calendar into a short reference the variant
    agent can stay consistent with, without re-sending the full calendar."""
    days = (content or {}).get("days", [])
    if not days:
        return "No content calendar available."

    return "\n".join(
        f'- Day {day.get("day")}: {day.get("post_idea", "")} (hook: "{day.get("hook", "")}")'
        for day in days
    )


def build_variant_input(marketing: dict, content: dict | None = None) -> dict:
    """
    Build a Creative Brief from the Marketing Strategy and Content Calendar.
    The Variant Agent should transform this brief into ad copy,
    not invent a new marketing strategy.
    """

    return {

        "content_calendar_summary": _summarize_content_calendar(content),


        # Campaign
        "campaign_goal":
            marketing.get(
                "data_sources",
                {}
            ).get(
                "primary_goal",
                ""
            ),

        # Audience
        "target_audience":
            ", ".join(
                marketing.get(
                    "stp_analysis",
                    {}
                ).get(
                    "attributes",
                    {}
                ).get(
                    "target_audience",
                    []
                )
            ),

        # Brand
        "brand_voice":
            marketing.get(
                "content_strategy",
                {}
            ).get(
                "attributes",
                {}
            ).get(
                "brand_voice",
                ""
            ),

        "brand_message":
            marketing.get(
                "content_strategy",
                {}
            ).get(
                "attributes",
                {}
            ).get(
                "brand_message",
                ""
            ),

        "storytelling_angle":
            marketing.get(
                "content_strategy",
                {}
            ).get(
                "attributes",
                {}
            ).get(
                "storytelling_angle",
                ""
            ),

        # Value Proposition
        "value_proposition":
            marketing.get(
                "stp_analysis",
                {}
            ).get(
                "attributes",
                {}
            ).get(
                "value_proposition",
                ""
            ),

        # Ideas
        "campaign_ideas":
            marketing.get(
                "campaign_strategy",
                {}
            ).get(
                "attributes",
                {}
            ).get(
                "campaign_ideas",
                []
            ),

        # Promotions
        "discount_strategy":
            marketing.get(
                "pricing_strategy",
                {}
            ).get(
                "attributes",
                {}
            ).get(
                "discount_strategy",
                ""
            ),

        "promotional_tactics":
            marketing.get(
                "campaign_strategy",
                {}
            ).get(
                "attributes",
                {}
            ).get(
                "promotional_tactics",
                []
            ),

        # CTA
        "call_to_actions":
            marketing.get(
                "campaign_strategy",
                {}
            ).get(
                "attributes",
                {}
            ).get(
                "call_to_actions",
                []
            ),

        # Platform
        "platform":
            ", ".join(
                marketing.get(
                    "channel_strategy",
                    {}
                ).get(
                    "attributes",
                    {}
                ).get(
                    "social_platforms",
                    []
                )
            )
    }

# ============================================================
# BUILD USER PROMPT
# ============================================================

def build_user_prompt(
    data: dict,
    previous_hooks: list[str] | None = None,
    previous_ctas: list[str] | None = None,
) -> str:
    """
    previous_hooks / previous_ctas: hooks and CTAs already generated on
    earlier days of THIS SAME campaign. Pass these in every call so the
    model actually knows what it already wrote, instead of just being told
    "don't repeat yourself" with nothing to compare against.
    """

    return VARIANT_TASK_PROMPT.format(

        content_calendar_summary=data["content_calendar_summary"],

        campaign_goal=data["campaign_goal"],

        target_audience=data["target_audience"],

        platform=data["platform"],

        brand_voice=data["brand_voice"],

        brand_message=data["brand_message"],

        value_proposition=data["value_proposition"],

        storytelling_angle=data["storytelling_angle"],

        campaign_ideas="\n".join(
            f"- {i}" for i in data["campaign_ideas"]
        ),

        discount_strategy=data["discount_strategy"],

        promotional_tactics="\n".join(
            f"- {i}" for i in data["promotional_tactics"]
        ),

        call_to_actions="\n".join(
            f"- {i}" for i in data["call_to_actions"]
        ),

        previous_hooks=format_used_list(previous_hooks, "hooks"),

        previous_ctas=format_used_list(previous_ctas, "CTAs"),

        banned_openers=format_used_list(BANNED_OPENERS, "openers"),

        banned_ctas=format_used_list(BANNED_CTA_PATTERNS, "CTA patterns"),

        banned_words=format_used_list(BANNED_WORDS_OVERUSED, "words"),
    )


def extract_hooks_and_ctas(variant_result: dict) -> tuple[list[str], list[str]]:
    """
    Pull the hook and cta out of variant_a/b/c from a generated result, so
    the caller (the day-by-day loop) can accumulate them and feed them back
    in as previous_hooks/previous_ctas on the next day's call.
    """
    hooks, ctas = [], []
    for key in ("variant_a", "variant_b", "variant_c"):
        variant = variant_result.get(key) or {}
        if variant.get("hook"):
            hooks.append(variant["hook"])
        if variant.get("cta"):
            ctas.append(variant["cta"])
    return hooks, ctas
# ============================================================
# ENSURE OUTPUT SHAPE
# ============================================================

def _ensure_shape(data: dict) -> dict:
    """
    Ensure every variant exists.
    """

    defaults = {
        "metadata": {
            "agent": "variant",
            "schema_version": "1.0.0",
            "status": "success",
        },
        "variant_a": {
            "angle": "Emotional",
            "hook": "",
            "body": "",
            "cta": "",
        },
        "variant_b": {
            "angle": "Rational",
            "hook": "",
            "body": "",
            "cta": "",
        },
        "variant_c": {
            "angle": "Urgency",
            "hook": "",
            "body": "",
            "cta": "",
        },
    }

    for key, value in defaults.items():
        if key not in data or data[key] is None:
            data[key] = value

    return data


# ============================================================
# GENERATE VARIANTS
# ============================================================

def generate_variants(
    marketing_strategy: dict,
    content: dict | None = None,
    model: str | None = None,
    settings_overrides: dict | None = None,
    previous_hooks: list[str] | None = None,
    previous_ctas: list[str] | None = None,
) -> dict:
    """
    Generate A/B/C ad variants from Marketing Strategy and Content Calendar.

    previous_hooks / previous_ctas: pass in the hooks/CTAs already generated
    on earlier days of this campaign (see extract_hooks_and_ctas below) so
    the model avoids repeating them.
    """

    if not marketing_strategy:
        return {
            "error": "Missing Marketing Strategy"
        }

    variant_input = build_variant_input(marketing_strategy, content)

    user_prompt = build_user_prompt(variant_input, previous_hooks, previous_ctas)

    settings = AGENT_SETTINGS["variant"].copy()
    if settings_overrides:
        settings.update(settings_overrides)

    agent = BaseAgent(
        system_prompt=VARIANT_SYSTEM_PROMPT,
        settings=settings,
        model=model,
    )

    try:
        result = agent.generate(user_prompt)

    except Exception as exc:
        return {
            "error": str(exc),
            "metadata": {
                "agent": "variant",
                "status": "failed",
            },
        }

    if "error" in result:
        return result

    result = _ensure_shape(result)

    result = validate_output(
        result,
        "variant",
    )

    result["metadata"]["status"] = "success"

    result["data_sources"] = {
    "used_marketing_strategy": True,
    "used_content_calendar": bool(content),
    "generated_variants": 3,
    "campaign_goal": variant_input["campaign_goal"],
    "platform": variant_input["platform"],
    "brand_voice": variant_input["brand_voice"],
}

    return result