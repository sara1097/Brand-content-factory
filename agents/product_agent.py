"""
Product Intelligence Agent

Extracts structured Product Intelligence
using the Vision Extraction Agent.
"""

from agents.vision_agent import extract_visual_information


def analyze_product(
    text_description: str,
    image_path: str | None = None,
    model: str | None = None,
    max_completion_tokens: int = 1500,
) -> dict:
    """
    Analyze a product using text and optional image.
    """

    vision_result = extract_visual_information(
        text_description=text_description,
        image_path=image_path,
        model=model,
        max_completion_tokens=max_completion_tokens,
    )

    return vision_result