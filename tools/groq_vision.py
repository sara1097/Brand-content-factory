"""
Reusable Groq Vision Client
"""

from __future__ import annotations

import base64
import io
import json
import os
from typing import Any

from PIL import Image

from config import PRODUCT_MODEL
from tools.groq_client import create_chat_completion

# Longest side an uploaded image is downscaled to before being sent to Groq.
# Unresized phone photos can be several MB; larger requests take longer and
# are more exposed to timeouts/transient capacity errors on Groq's side, and
# cost more vision tokens for no accuracy benefit at this resolution.
MAX_IMAGE_DIMENSION = 1024
JPEG_QUALITY = 85


# ==========================================================
# IMAGE
# ==========================================================

def encode_image(image_path: str) -> str:
    """
    Downscale the image (longest side capped at MAX_IMAGE_DIMENSION) and
    re-encode as JPEG before base64-encoding.
    """
    abs_path = os.path.abspath(image_path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Image not found: {abs_path}")

    with Image.open(abs_path) as image:
        image = image.convert("RGB")
        image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ==========================================================
# GROQ VISION
# ==========================================================

def call_groq_vision(
    prompt: str,
    image_b64: str | None = None,
    model: str | None = None,
    max_completion_tokens: int = 1500,
) -> str | None:
    """
    Call Groq Vision API with an optional base64 image.
    """
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    if image_b64:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"
                },
            }
        )

    response = create_chat_completion(
        model=model or PRODUCT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Return ONLY valid JSON.",
            },
            {
                "role": "user",
                "content": content,
            },
        ],
        temperature=0.2,
        max_completion_tokens=max_completion_tokens,
    )

    return response.choices[0].message.content


# ==========================================================
# JSON PARSER
# ==========================================================

def parse_json_response(text: str | None) -> dict:
    """
    Parse the string response into a JSON dictionary safely.
    """
    if not text:
        return {"error": "Received empty response from API."}

    cleaned = text.strip()

    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(cleaned)
    
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                pass

        return {
            "error": "JSON parse failed",
            "raw_output": text,
        }