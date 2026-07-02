"""
Vision Extraction Agent

Extracts only the raw visual information from
the product image.

This agent does NOT perform:

- Quality Assessment
- Market Research
- Marketing
- Product Intelligence
"""

from tools.groq_vision import (
    call_groq_vision,
    encode_image,
    parse_json_response,
)

from agents.prompts.vision_prompt import VISION_PROMPT


def extract_visual_information(
    text_description: str,
    image_path: str | None = None,
    model: str | None = None,
    max_completion_tokens: int = 1500,
) -> dict:

    try:
        image_b64 = encode_image(image_path) if image_path else None
    except Exception as exc:
        return {"error": str(exc)}

    prompt = f"""
TEXT DESCRIPTION

{text_description}

Extract the visual information only.
"""

    try:
        raw = call_groq_vision(
            prompt=f"{VISION_PROMPT}\n\n{prompt}",
            image_b64=image_b64,
            model=model,
            max_completion_tokens=max_completion_tokens,
        )
    except Exception as exc:
        return {"error": str(exc)}

    return parse_json_response(raw)