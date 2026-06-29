"""
Compliance Agent

Reviews marketing ad variants and rewrites any
content that violates advertising policies.
"""

from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.prompts.constants import AGENT_SETTINGS
from core.validator import validate_output

from agents.prompts.compliance_prompt import (
    COMPLIANCE_SYSTEM_PROMPT,
    COMPLIANCE_TASK_PROMPT,
)

def build_compliance_input(
    marketing: dict,
    variants: dict,
) -> dict:
    """
    Build Compliance input using BOTH
    Marketing Strategy and Variant output.
    """

    return {

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

        "recommended_cta":
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

        "variant_a":
            variants.get("variant_a", {}),

        "variant_b":
            variants.get("variant_b", {}),

        "variant_c":
            variants.get("variant_c", {}),
    }

def build_user_prompt(data: dict) -> str:

    return COMPLIANCE_TASK_PROMPT.format(

        discount_strategy=data["discount_strategy"],

        promotional_tactics="\n".join(
            f"- {x}"
            for x in data["promotional_tactics"]
        ),

        recommended_cta="\n".join(
            f"- {x}"
            for x in data["recommended_cta"]
        ),

        variant_a=data["variant_a"],

        variant_b=data["variant_b"],

        variant_c=data["variant_c"],

    )
# ============================================================
# ENSURE OUTPUT SHAPE
# ============================================================

def _ensure_shape(data: dict) -> dict:
    """
    Ensure every compliance result exists.
    """

    defaults = {

        "metadata": {

            "agent": "compliance",

            "schema_version": "1.0.0",

            "status": "success"

        },

        "variant_a": {

            "safe_campaign_text": {

                "hook": "",

                "body": "",

                "cta": ""

            },

            "compliance_flags": [],

          "explanation_of_modifications": ""

        },

        "variant_b": {

            "safe_campaign_text": {

                "hook": "",

                "body": "",

                "cta": ""

            },

            "compliance_flags": [],

            "explanation_of_modifications": ""

        },

        "variant_c": {

            "safe_campaign_text": {

                "hook": "",

                "body": "",

                "cta": ""

            },

            "compliance_flags": [],

            "explanation_of_modifications": ""

        }

    }

    for key, value in defaults.items():

        if key not in data or data[key] is None:

            data[key] = value

    return data


# ============================================================
# GENERATE COMPLIANCE
# ============================================================

def generate_compliance(
    marketing_strategy: dict,
    variants: dict,
) -> dict:

    """
    Review Variant Agent output and produce
    policy-compliant ad variants.
    """

    if not marketing_strategy:

        return {
            "error": "Missing Marketing Strategy"
        }

    if not variants:

        return {
            "error": "Missing Variant output"
        }

    compliance_input = build_compliance_input(
    marketing_strategy,
    variants,
    )
    user_prompt = build_user_prompt(compliance_input)

    agent = BaseAgent(

        system_prompt=COMPLIANCE_SYSTEM_PROMPT,

        settings=AGENT_SETTINGS["compliance"]

    )

    try:

        result = agent.generate(user_prompt)

    except Exception as exc:

        return {

            "error": str(exc),

            "metadata": {

                "agent": "compliance",

                "status": "failed"

            }

        }

    if "error" in result:

        return result

    result = _ensure_shape(result)

    result = validate_output(
        result,
        "compliance"
    )

    result["metadata"]["status"] = "success"

    result["data_sources"] = {

    "used_marketing_strategy": True,

    "used_variant_agent": True,

    "reviewed_variants": 3

}
    return result
