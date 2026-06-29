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
)

# ============================================================
# BUILD VARIANT INPUT
# ============================================================

def build_variant_input(marketing: dict) -> dict:
    """
    Build a Creative Brief from the Marketing Strategy.
    The Variant Agent should transform this brief into ad copy,
    not invent a new marketing strategy.
    """

    return {

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

def build_user_prompt(data: dict) -> str:
    

    return VARIANT_TASK_PROMPT.format(

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
    )
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

def generate_variants(marketing_strategy: dict) -> dict:
    """
    Generate A/B/C ad variants from Marketing Strategy.
    """

    if not marketing_strategy:
        return {
            "error": "Missing Marketing Strategy"
        }

    variant_input = build_variant_input(marketing_strategy)

    user_prompt = build_user_prompt(variant_input)

    agent = BaseAgent(
        system_prompt=VARIANT_SYSTEM_PROMPT,
        settings=AGENT_SETTINGS["variant"],
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
    "generated_variants": 3,
    "campaign_goal": variant_input["campaign_goal"],
    "platform": variant_input["platform"],
    "brand_voice": variant_input["brand_voice"],
}

    return result

    