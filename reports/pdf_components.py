"""
pdf_components.py

Reusable PDF components for ReportLab.
"""

import re

from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import inch

_DASH_LINE = re.compile(r"^-{3,}$")
_EQUALS_LINE = re.compile(r"^={3,}$")


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
# NARRATIVE TEXT
# ============================================================

def add_narrative_text(story, text, styles):
    """
    Render the report's plain-text narrative (see
    agents/report_agent.py::_build_narrative_report) into the PDF as real
    headings, bullet lists, and paragraphs -- instead of dumping the raw
    report structure as one block of text.
    """
    lines = text.splitlines()

    # The narrative always opens with "EXECUTIVE BUSINESS REPORT" + a "="
    # separator -- already covered by add_title/add_subtitle, so skip it.
    if lines and lines[0].strip().upper() == "EXECUTIVE BUSINESS REPORT":
        lines = lines[1:]
        if lines and _EQUALS_LINE.match(lines[0].strip()):
            lines = lines[1:]

    bullets: list[str] = []

    def flush_bullets():
        if bullets:
            add_bullets(story, list(bullets), styles)
            bullets.clear()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        if _EQUALS_LINE.match(line):
            i += 1
            continue

        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if _DASH_LINE.match(next_line):
            flush_bullets()
            add_heading(story, line.title(), styles)
            i += 2
            continue

        if line.startswith("- "):
            bullets.append(line[2:])
            i += 1
            continue

        flush_bullets()
        add_paragraph(story, line, styles)
        i += 1

    flush_bullets()