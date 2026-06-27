"""
Reusable Groq API Client
"""

import base64
import json
import os

from groq import Groq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
)

client = Groq(
    api_key=GROQ_API_KEY
)


# ==========================================================
# IMAGE
# ==========================================================

def encode_image(image_path: str) -> str:
    """
    Convert image to base64.
    """

    abs_path = os.path.abspath(image_path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(
            f"Image not found: {abs_path}"
        )

    with open(abs_path, "rb") as f:
        return base64.b64encode(
            f.read()
        ).decode("utf-8")
# ==========================================================
# GROQ CHAT
# ==========================================================

def call_groq(
    messages: list,
    temperature: float = 0.2,
    top_p: float = 0.9,
    top_k: int = 40,
    repeat_penalty: float = 1.1,
    num_ctx: int = 8192,
    num_predict: int = 1500,
    model: str | None = None,
) -> str:
    """
    Generic Groq Chat Client.

    Extra parameters are accepted for compatibility
    with the old Ollama client.
    """

    response = client.chat.completions.create(
        model=model or GROQ_MODEL,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content
# ==========================================================
# JSON PARSER
# ==========================================================

def parse_json_response(
    text: str,
    retry_messages: list | None = None,
    max_retries: int = 0,
) -> dict:
    """
    Parse JSON returned from Groq.
    """

    cleaned = text.strip()

    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()

    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(cleaned)

    except Exception:

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            try:
                return json.loads(
                    cleaned[start:end + 1]
                )
            except Exception:
                pass

        return {
            "error": "JSON parse failed",
            "raw_output": text
        }