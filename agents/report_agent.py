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

# Internal bookkeeping keys that don't carry substantive report content --
# stripped from the prompt to keep token cost down without losing anything
# the report agent actually needs to reason about.
_NOISE_KEYS = {"data_sources", "metadata", "evidence", "strategy_score"}

_SECTION_TITLES = {
    "executive_summary": "Executive Summary",
    "product_assessment": "Product Assessment",
    "market_assessment": "Market Assessment",
    "marketing_assessment": "Marketing Assessment",
    "swot_summary": "SWOT Summary",
    "strategic_recommendations": "Strategic Recommendations",
    "implementation_roadmap": "Implementation Roadmap",
    "kpi_framework": "KPI Framework",
    "executive_verdict": "Executive Verdict",
}


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


def _trim(data: dict | None) -> dict:
    """Drop internal bookkeeping fields before embedding in the prompt."""
    if not data:
        return {}
    return {k: v for k, v in data.items() if k not in _NOISE_KEYS}


# ============================================================
# PLAIN-TEXT NARRATIVE (built locally, no extra LLM call/tokens)
# ============================================================

def _render_value(value, indent: int = 0) -> list[str]:
    pad = "  " * indent
    lines: list[str] = []

    if isinstance(value, dict):
        for key, sub_value in value.items():
            label = str(key).replace("_", " ").strip().title()
            if isinstance(sub_value, (dict, list)) and sub_value:
                lines.append(f"{pad}{label}:")
                lines.extend(_render_value(sub_value, indent + 1))
            else:
                lines.append(f"{pad}{label}: {sub_value}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                lines.extend(_render_value(item, indent))
                lines.append("")
            else:
                lines.append(f"{pad}- {item}")
    else:
        lines.append(f"{pad}{value}")

    return lines


def _build_narrative_report(result: dict) -> str:
    """
    Render the structured report as a readable plain-text document for
    direct display to a non-technical user, built deterministically from
    the already-generated JSON (no additional API call/token cost).
    """
    lines: list[str] = ["EXECUTIVE BUSINESS REPORT", "=" * 60, ""]

    for key, title in _SECTION_TITLES.items():
        section = result.get(key)
        if not section:
            continue
        lines.append(title.upper())
        lines.append("-" * len(title))
        lines.extend(_render_value(section))
        lines.append("")

    return "\n".join(lines).strip()


# ============================================================
# GENERATE EXECUTIVE REPORT
# ============================================================

def generate_report(
    product_intelligence,
    market_intelligence,
    marketing_strategy,
    variants: dict | None = None,
    compliance: dict | None = None,
    content: dict | None = None,
    model: str | None = None,
    settings_overrides: dict | None = None,
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

    variants = variants or {}
    compliance = compliance or {}
    content = content or {}

    settings = AGENT_SETTINGS["report"].copy()
    if settings_overrides:
        settings.update(settings_overrides)

    agent = BaseAgent(
        system_prompt=REPORT_SYSTEM_PROMPT,
        settings=settings,
        model=model,
    )

    user_prompt = f"""
==================================================
PRODUCT INTELLIGENCE
==================================================

{json.dumps(_trim(product_intelligence), indent=2, ensure_ascii=False)}

==================================================
MARKET INTELLIGENCE
==================================================

{json.dumps(_trim(market_intelligence), indent=2, ensure_ascii=False)}

==================================================
MARKETING STRATEGY
==================================================

{json.dumps(_trim(marketing_strategy), indent=2, ensure_ascii=False)}

==================================================
AD VARIANTS
==================================================

{json.dumps(_trim(variants), indent=2, ensure_ascii=False)}

==================================================
COMPLIANCE REVIEW
==================================================

{json.dumps(_trim(compliance), indent=2, ensure_ascii=False)}

==================================================
CONTENT CALENDAR
==================================================

{json.dumps(_trim(content), indent=2, ensure_ascii=False)}

==================================================
TASK
==================================================

Generate the FINAL Executive Business Report.

Use ALL available information:

• Product Intelligence
• Market Intelligence
• Marketing Strategy
• Generated Ad Variants
• Compliance Review

The report must summarize:

• Product strengths
• Market opportunities
• Marketing strategy
• Generated campaigns
• Compliance observations
• Final approved marketing direction

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
        "used_marketing_strategy": True,
        "used_variant_agent": bool(variants),
        "used_compliance_agent": bool(compliance),
        "used_content_agent": bool(content),
    }

    # ============================================================
    # PLAIN-TEXT VERSION (for direct display to a non-technical user)
    # ============================================================

    result["narrative_report"] = _build_narrative_report(result)

    return result
