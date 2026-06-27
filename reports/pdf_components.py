"""
pdf_components.py

Reusable PDF components for ReportLab.
"""

from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import inch


# ============================================================
# TITLE
# ============================================================

def add_title(story, text, styles):
    """Add report title."""
    story.append(
        Paragraph(
            text,
            styles["title"]
        )
    )
    story.append(
        Spacer(
            1,
            0.35 * inch
        )
    )


# ============================================================
# SUBTITLE
# ============================================================

def add_subtitle(story, text, styles):
    """Add report subtitle."""
    story.append(
        Paragraph(
            text,
            styles["subtitle"]
        )
    )
    story.append(
        Spacer(
            1,
            0.25 * inch
        )
    )


# ============================================================
# HEADING
# ============================================================

def add_heading(story, text, styles):
    """Add section heading."""
    story.append(
        Paragraph(
            text,
            styles["heading"]
        )
    )
    story.append(
        Spacer(
            1,
            0.15 * inch
        )
    )


# ============================================================
# PARAGRAPH
# ============================================================

def add_paragraph(story, text, styles):
    """Add paragraph."""
    story.append(
        Paragraph(
            str(text),
            styles["body"]
        )
    )
    story.append(
        Spacer(
            1,
            0.20 * inch
        )
    )


# ============================================================
# BULLET LIST
# ============================================================

def add_bullets(story, items, styles):
    """Add bullet list."""

    if not items:
        return

    for item in items:
        story.append(
            Paragraph(
                f"• {item}",
                styles["body"]
            )
        )

    story.append(
        Spacer(
            1,
            0.20 * inch
        )
    )


# ============================================================
# SECTION
# ============================================================

def add_section(story, title, content, styles):
    print("NEW PDF COMPONENTS")
    add_heading(
        story,
        title,
        styles,
    )

    def render(value):

        if isinstance(value, dict):

            for k, v in value.items():

                add_heading(
                    story,
                    k.replace("_", " ").title(),
                    styles,
                )

                render(v)

        elif isinstance(value, list):

            if all(not isinstance(i, (dict, list)) for i in value):

                add_bullets(
                    story,
                    value,
                    styles,
                )

            else:

                for item in value:
                    render(item)

        else:

            add_paragraph(
                story,
                value,
                styles,
            )

    render(content)