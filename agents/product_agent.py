"""
Product Intelligence Agent

Extracts structured Product Intelligence from
text descriptions and optional product images.

This agent is responsible ONLY for product understanding.

It does NOT perform:

- Market Research
- Competitor Analysis
- Marketing Strategy
- Pricing Analysis
- Executive Reporting
"""

from agents.prompts.product_prompt import PRODUCT_SYSTEM_PROMPT
from agents.prompts.constants import AGENT_SETTINGS

from tools.ollama_client import (
    call_ollama,
    encode_image,
    parse_json_response,
)


def analyze_product(
    text_description: str,
    image_path: str | None = None
) -> dict:
    """
    Analyze a product using text and optional image.

    Parameters
    ----------
    text_description : str
        Product description.

    image_path : str | None
        Optional product image.

    Returns
    -------
    dict
        Structured Product Intelligence JSON.
    """

    image_b64 = encode_image(image_path) if image_path else None

    image_status = (
        "Product image is provided."
        if image_b64
        else "No product image is available."
    )

    user_prompt = f"""
==================================================
PRODUCT INPUT
==================================================

TEXT DESCRIPTION

{text_description}

==================================================
IMAGE STATUS
==================================================

{image_status}

==================================================
TASK
==================================================

Build Product Intelligence.

Analyze ONLY the product.

Use every available piece of evidence.

Extract:

• Product Identity

• Visual Intelligence

• Construction Intelligence

• Feature Intelligence

• Quality Intelligence

Do NOT perform:

• Market Research

• Competitor Analysis

• Marketing Strategy

• SWOT

• Pricing

If information cannot be verified,
leave it empty or unknown according to the schema.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

No markdown.

No explanations.

No comments.

No extra text.
"""

    user_message = {
        "role": "user",
        "content": user_prompt,
    }

    if image_b64:
        user_message["images"] = [image_b64]

    messages = [
        {
            "role": "system",
            "content": PRODUCT_SYSTEM_PROMPT,
        },
        user_message,
    ]

    settings = AGENT_SETTINGS["product"]

    raw_output = call_ollama(
        messages=messages,
        **settings,
    )

    product_intelligence = parse_json_response(
        raw_output,
        retry_messages=messages,
    )

    return product_intelligence