"""
Reusable Ollama API client
"""

from __future__ import annotations

import os
import re
import json
import base64
import requests

from config import OLLAMA_MODEL, OLLAMA_URL, TIMEOUT

# ============================================================
# IMAGE
# ============================================================

def encode_image(image_path: str) -> str:
    """
    Convert an image into Base64.
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


# ============================================================
# OLLAMA CLIENT
# ============================================================

def call_ollama(
    messages: list,
    temperature: float = 0.2,
    top_p: float = 0.9,
    top_k: int = 40,
    repeat_penalty: float = 1.1,
    num_ctx: int = 8192,
    num_predict: int = 2000,
    model: str | None = None,
) -> str:
    """
    Generic Ollama Chat API Client.
    """

    payload = {

        "model": model or OLLAMA_MODEL,
        "messages": messages,

        "stream": False,

        "format": "json",

        "think": False,

        "keep_alive": "10m",

        "options": {

            "temperature": temperature,

            "top_p": top_p,

            "top_k": top_k,

            "repeat_penalty": repeat_penalty,

            "num_ctx": num_ctx,

            "num_predict": num_predict,

        },

    }

    try:

        response = requests.post(

            f"{OLLAMA_URL}/api/chat",

            json=payload,

            timeout=TIMEOUT,

        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"]

    except requests.exceptions.ConnectionError:

        raise Exception(
            "Cannot connect to Ollama. "
            "Make sure Ollama is running."
        )

    except requests.exceptions.ReadTimeout:

        raise TimeoutError(
            f"Ollama exceeded timeout ({TIMEOUT}s)."
        )

    except Exception as exc:

        raise Exception(
            f"Ollama Error: {exc}"
        )


# ============================================================
# EMBEDDINGS
# ============================================================

def get_embedding(
    text: str,
) -> list:
    """
    Generate embedding vector.
    """

    try:

        response = requests.post(

            f"{OLLAMA_URL}/api/embeddings",

            json={

                "model": OLLAMA_MODEL,

                "prompt": text,

            },

            timeout=60,

        )

        response.raise_for_status()

        return response.json()["embedding"]

    except Exception as exc:

        print(f"Embedding Error: {exc}")

        return []


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(
    text: str,
) -> str:
    """
    Extract the first JSON object from text.
    """

    text = text.strip()

    if "```json" in text:

        text = text.split(
            "```json",
            1,
        )[1]

        text = text.split(
            "```",
            1,
        )[0]

    elif "```" in text:

        text = text.split(
            "```",
            1,
        )[1]

        text = text.split(
            "```",
            1,
        )[0]

    match = re.search(

        r"\{.*\}",

        text,

        flags=re.DOTALL,

    )

    if match:

        return match.group(0)

    return text
# ============================================================
# JSON PARSER
# ============================================================

def parse_json_response(
    text: str,
    retry_messages: list | None = None,
    max_retries: int = 2,
) -> dict:
    """
    Parse JSON returned by Ollama.

    Automatically:

    • removes markdown
    • extracts JSON
    • retries if JSON is invalid
    • returns useful debugging information
    """

    cleaned = extract_json(text)

    try:

        return json.loads(cleaned)

    except json.JSONDecodeError as exc:

        print(f"\nJSON Parse Error: {exc}\n")

        if retry_messages and max_retries > 0:

            print(
                f"Retrying JSON generation "
                f"({max_retries} retries left)..."
            )

            repair_messages = retry_messages + [

                {
                    "role": "assistant",
                    "content": text,
                },

                {
                    "role": "user",
                    "content":
                    """
Your previous response contained invalid or truncated JSON.

Rewrite the ENTIRE response.

Rules:

1. Return ONLY JSON.
2. Do NOT use Markdown.
3. Do NOT explain anything.
4. Do NOT truncate the output.
5. Ensure every object and array is closed.
6. Ensure every string is properly quoted.
7. Follow the schema exactly.
"""
                }

            ]

            repaired = call_ollama(

    messages=repair_messages,

    temperature=0.1,

    top_p=0.9,

    top_k=40,

    repeat_penalty=1.05,

    num_ctx=8192,

    num_predict=4000,

)

            return parse_json_response(

                repaired,

                retry_messages=retry_messages,

                max_retries=max_retries - 1,

            )

        return {

            "error": "JSON parse failed",

            "details": str(exc),

            "raw_output": text,

        }


# ============================================================
# JSON VALIDATION
# ============================================================

def is_valid_json(text: str) -> bool:
    """
    Check whether a string is valid JSON.
    """

    try:

        json.loads(
            extract_json(text)
        )

        return True

    except Exception:

        return False