"""
pdf_styles.py

Shared PDF styles.
"""

from reportlab.lib.styles import getSampleStyleSheet

from reportlab.lib.enums import TA_CENTER, TA_LEFT

from reportlab.lib.colors import HexColor


def build_styles():

    styles = getSampleStyleSheet()

    title = styles["Title"]

    title.alignment = TA_CENTER

    title.textColor = HexColor("#0F172A")



    subtitle = styles["Heading2"]

    subtitle.alignment = TA_CENTER

    subtitle.textColor = HexColor("#334155")



    heading = styles["Heading1"]

    heading.textColor = HexColor("#1E40AF")



    body = styles["BodyText"]

    body.alignment = TA_LEFT

    body.leading = 20



    return {

        "title": title,

        "subtitle": subtitle,

        "heading": heading,

        "body": body,

    }