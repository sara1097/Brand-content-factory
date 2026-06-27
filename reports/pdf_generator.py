"""
pdf_generator.py

Generate Executive PDF directly from report JSON.
"""

from reportlab.platypus import SimpleDocTemplate

from reports.pdf_styles import build_styles
from reports.pdf_components import (
    add_title,
    add_subtitle,
    add_section,
)


def generate_pdf(report: dict, output_path: str):

    styles = build_styles()

    doc = SimpleDocTemplate(
        output_path,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    story = []

    # ==========================================================
    # TITLE
    # ==========================================================

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

    # ==========================================================
    # CONTENT
    # ==========================================================

    for key, value in report.items():

        if key == "metadata":
            continue

        section_title = key.replace("_", " ").title()

        add_section(
            story,
            section_title,
            str(value),
            styles,
        )

    doc.build(story)

    return output_path