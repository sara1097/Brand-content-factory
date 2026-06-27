from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from agents.prompts.marketing_prompt import MARKETING_SYSTEM_PROMPT
from agents.prompts.constants import AGENT_SETTINGS
from core.validator import validate_output


# ============================================================
# DEFAULT CONSTRAINTS
# ============================================================

DEFAULT_CONSTRAINTS = {
    "country": "Egypt",
    "budget": "Medium",
    "campaign_duration": "6 Months",
    "primary_goal": "Increase Sales",
    "brand_stage": "New Product Launch",
}


# ============================================================
# ENSURE OUTPUT SHAPE
# ============================================================

def _ensure_shape(data: dict) -> dict:
    """
    Ensure the returned JSON always contains all required
    top-level sections.
    """

    defaults = {
        "metadata": {
            "agent": "marketing_strategy",
            "schema_version": "1.0.0",
            "status": "success",
        },
        "executive_strategy": {},
        "stp_analysis": {},
        "swot_analysis": {},
        "pricing_strategy": {},
        "go_to_market_strategy": {},
        "channel_strategy": {},
        "content_strategy": {},
        "campaign_strategy": {},
        "budget_strategy": {},
        "kpi_framework": {},
        "risk_management": {},
    }

    for key, value in defaults.items():
        if key not in data or data[key] is None:
            data[key] = value

    return data


# ============================================================
# BUILD MARKETING STRATEGY
# ============================================================

def build_marketing_strategy(
    product_intelligence: dict,
    market_intelligence: dict,
    business_constraints: dict | None = None,
) -> dict:
    """
    Build an executive marketing strategy from:

    - Product Intelligence
    - Market Intelligence
    - Business Constraints
    """

    if not product_intelligence:
        return {
            "error": "Missing Product Intelligence"
        }

    if not market_intelligence:
        return {
            "error": "Missing Market Intelligence"
        }

    constraints = DEFAULT_CONSTRAINTS.copy()

    if business_constraints:
        constraints.update(business_constraints)

    agent = BaseAgent(
        system_prompt=MARKETING_SYSTEM_PROMPT,
        settings=AGENT_SETTINGS["marketing"],
    )
    
    marketing_input = {
        "product": {
            "identity": product_intelligence.get("identity_intelligence"),
            "features": product_intelligence.get("feature_intelligence"),
            "quality": product_intelligence.get("quality_intelligence"),
        },
        "market": {
            "executive_summary": market_intelligence.get("executive_summary"),
            "competitive_analysis": market_intelligence.get("competitive_analysis"),
            "consumer_intelligence": market_intelligence.get("consumer_intelligence"),
        },
    }
    
    # Serialize dictionaries to JSON strings to avoid f-string curly brace errors
    marketing_input_json = json.dumps(marketing_input, indent=2, ensure_ascii=False)
    constraints_json = json.dumps(constraints, indent=2, ensure_ascii=False)

    user_prompt = f"""
==================================================
INPUT DATA
==================================================
BUSINESS CONSTRAINTS:
{constraints_json}

INTELLIGENCE DATA:
{marketing_input_json}

==================================================
YOUR TASK
==================================================

Develop a complete executive-level Marketing Strategy.

The strategy MUST include:

• Executive Strategy
• STP Analysis
• SWOT Analysis
• Pricing Strategy
• Go-To-Market Strategy
• Channel Strategy
• Content Strategy
• Campaign Strategy
• Budget Strategy
• KPI Framework
• Risk Management

Every recommendation must:

- Be evidence-based
- Be business-oriented
- Be actionable
- Be measurable
- Be consistent with Product Intelligence
- Be consistent with Market Intelligence

Return ONLY valid JSON.
"""

    try:
        result = agent.generate(user_prompt)
        
        if isinstance(result, str):
            result = json.loads(result)

    except Exception as exc:
        return {
            "error": str(exc),
            "metadata": {
                "agent": "marketing_strategy",
                "status": "failed"
            }
        }

    if "error" in result:
        return result

    result = _ensure_shape(result)

    result = validate_output(
        result,
        "marketing"
    )

    result["metadata"]["status"] = "success"

    # ============================================================
    # DATA SOURCES
    # ============================================================

    result["data_sources"] = {
        "used_product_intelligence": True,
        "used_market_intelligence": True,
        "used_business_constraints": bool(business_constraints),
        "country": constraints.get("country"),
        "budget": constraints.get("budget"),
        "campaign_duration": constraints.get("campaign_duration"),
        "primary_goal": constraints.get("primary_goal"),
        "brand_stage": constraints.get("brand_stage")
    }

    # ============================================================
    # STRATEGY SCORE (Placeholder)
    # ============================================================

    result["strategy_score"] = {
        "overall_score": None,
        "market_fit": None,
        "execution_feasibility": None,
        "competitive_advantage": None,
        "confidence": None
    }

    print("=" * 60)
    print("Marketing Prompt Length")
    print(len(user_prompt))
    print("=" * 60)
    
    return result