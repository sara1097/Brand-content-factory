"""
pdf_generator.py

Generate the Executive PDF from the report's plain-text narrative.
"""

from reportlab.platypus import SimpleDocTemplate

from reports.pdf_styles import build_styles
from reports.pdf_components import (
    add_title,
    add_subtitle,
    add_narrative_text,
)


def generate_pdf(narrative_report: str, output_path: str):

    styles = build_styles()

    doc = SimpleDocTemplate(
        output_path,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    story = []

    add_title(
        story,
        "Enterprise AI Marketing Intelligence Report",
        styles,
    )

    add_subtitle(
        story,
        "Executive Business Report",
        styles,
    )

    add_narrative_text(story, narrative_report or "No report content available.", styles)

    doc.build(story)

    return output_path
