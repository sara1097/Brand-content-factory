"""
validator.py

Shared validation utilities for all AI agents.
"""

from __future__ import annotations
from typing import Any

# ============================================================
# REQUIRED KEYS
# ============================================================

REQUIRED_KEYS = {
    "product": [
        "metadata",
        "identity_intelligence",
        "visual_intelligence",
        "construction_intelligence",
        "feature_intelligence",
        "quality_intelligence",
        "limitations"
    ],
    "research": [
        "metadata",
        "market_intelligence",
        "competitive_intelligence",
        "pricing_intelligence",
        "consumer_intelligence",
        "channel_intelligence",
        "trend_intelligence",
        "limitations"
    ],
    "marketing": [
        "metadata",
        "executive_strategy",
        "stp_analysis",
        "swot_analysis",
        "pricing_strategy",
        "go_to_market_strategy",
        "channel_strategy",
        "content_strategy",
        "campaign_strategy",
        "budget_strategy",
        "kpi_framework",
        "risk_management"
    ],
    "variant": [
    "metadata",
    "variant_a",
    "variant_b",
    "variant_c"
],
"compliance": [

    "metadata",

    "variant_a",

    "variant_b",

    "variant_c"

],
    "report": [
        "metadata",
        "executive_summary",
        "product_assessment",
        "market_assessment",
        "marketing_assessment",
        "swot_summary",
        "strategic_recommendations",
        "implementation_roadmap",
        "kpi_framework",
        "executive_verdict"
    ]
}

# ============================================================
# VALIDATION
# ============================================================

def validate_schema(data: dict, schema_name: str) -> dict:
    """
    Ensure all required top-level keys exist.
    """
    required = REQUIRED_KEYS.get(schema_name, [])

    for key in required:
        if key not in data:
            data[key] = {}

    return data

# ============================================================
# RELIABILITY NORMALIZATION
# ============================================================

def normalize_reliability(data: Any):
    """
    Clamp every reliability value between 0.0 and 1.0.
    """
    if isinstance(data, dict):
        if "reliability" in data:
            try:
                value = float(data["reliability"])
            except Exception:
                value = 0.0

            value = max(0.0, min(1.0, value))
            data["reliability"] = value

        for value in data.values():
            normalize_reliability(value)

    elif isinstance(data, list):
        for item in data:
            normalize_reliability(item)

# ============================================================
# FINAL VALIDATION
# ============================================================

def validate_output(data: dict, schema_name: str) -> dict:
    """
    Run all validation steps.
    """
    data = validate_schema(data, schema_name)
    normalize_reliability(data)

    return data