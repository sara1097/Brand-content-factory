"""
Executive Report Agent

Generates an executive business report using:
- Product Intelligence
- Market Intelligence
- Marketing Strategy
"""

from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from agents.prompts.report_prompt import REPORT_SYSTEM_PROMPT
from agents.prompts.constants import AGENT_SETTINGS
from core.validator import validate_output


# ============================================================
# ENSURE OUTPUT SHAPE
# ============================================================

def _ensure_shape(data: dict) -> dict:
    """
    Ensure all report sections always exist.
    """

    defaults = {
        "metadata": {
            "agent": "executive_report",
            "schema_version": "1.0.0",
            "status": "success"
        },
        "executive_summary": {},
        "product_assessment": {},
        "market_assessment": {},
        "marketing_assessment": {},
        "swot_summary": {},
        "strategic_recommendations": {},
        "implementation_roadmap": {},
        "kpi_framework": {},
        "executive_verdict": {}
    }

    for key, value in defaults.items():
        if key not in data or data[key] is None:
            data[key] = value

    return data


# ============================================================
# GENERATE EXECUTIVE REPORT
# ============================================================

def generate_report(
    product_intelligence: dict,
    market_intelligence: dict,
    marketing_strategy: dict,
) -> dict:
    """
    Generate the final executive business report.
    """

    if not product_intelligence:
        return {
            "error": "Missing Product Intelligence"
        }

    if not market_intelligence:
        return {
            "error": "Missing Market Intelligence"
        }

    if not marketing_strategy:
        return {
            "error": "Missing Marketing Strategy"
        }

    agent = BaseAgent(
        system_prompt=REPORT_SYSTEM_PROMPT,
        settings=AGENT_SETTINGS["report"]
    )

    user_prompt = f"""
==================================================
PRODUCT INTELLIGENCE
==================================================

{json.dumps(product_intelligence, indent=2, ensure_ascii=False)}

==================================================
MARKET INTELLIGENCE
==================================================

{json.dumps(market_intelligence, indent=2, ensure_ascii=False)}

==================================================
MARKETING STRATEGY
==================================================

{json.dumps(marketing_strategy, indent=2, ensure_ascii=False)}

==================================================
TASK
==================================================

Generate a complete Executive Business Report.

The report must include:

• Executive Summary
• Product Assessment
• Market Assessment
• Marketing Assessment
• SWOT Summary
• Strategic Recommendations
• Implementation Roadmap
• KPI Framework
• Executive Verdict

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
                "agent": "executive_report",
                "status": "failed"
            }
        }

    if "error" in result:
        return result

    result = _ensure_shape(result)

    result = validate_output(
        result,
        "report"
    )

    result["metadata"]["status"] = "success"

    # ============================================================
    # DATA SOURCES
    # ============================================================

    result["data_sources"] = {
        "used_product_intelligence": True,
        "used_market_intelligence": True,
        "used_marketing_strategy": True
    }

    return result
