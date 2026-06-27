"""
report_formatter.py

Formats the Executive Report into a clean structure
that can be rendered as PDF, HTML, or Markdown.
"""

from __future__ import annotations


def _section(title: str, content):
    """Create a standard report section."""
    return {
        "title": title,
        "content": content,
    }


def format_report(report: dict) -> dict:
    """
    Convert the raw Executive Report JSON into
    a presentation-friendly structure.
    """

    metadata = report.get("metadata", {})

    sections = [

        _section(
            "Executive Summary",
            report.get("executive_summary", {})
        ),

        _section(
            "Product Assessment",
            report.get("product_assessment", {})
        ),

        _section(
            "Market Assessment",
            report.get("market_assessment", {})
        ),

        _section(
            "Marketing Assessment",
            report.get("marketing_assessment", {})
        ),

        _section(
            "SWOT Analysis",
            report.get("swot_summary", {})
        ),

        _section(
            "Strategic Recommendations",
            report.get("strategic_recommendations", {})
        ),

        _section(
            "Implementation Roadmap",
            report.get("implementation_roadmap", {})
        ),

        _section(
            "KPI Framework",
            report.get("kpi_framework", {})
        ),

        _section(
            "Executive Verdict",
            report.get("executive_verdict", {})
        ),

    ]

    return {

        "title": "Executive Business Intelligence Report",

        "subtitle": (
            "AI-Powered Product, Market & Marketing Intelligence"
        ),

        "metadata": metadata,

        "sections": sections

    }
