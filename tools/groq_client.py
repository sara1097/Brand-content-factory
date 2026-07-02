"""
Reusable Groq API Client
"""

import base64
import json
import os
import re
import time
from typing import Callable, TypeVar

from groq import (
    APIConnectionError,
    BadRequestError,
    Groq,
    InternalServerError,
    RateLimitError,
)

from config import (
    GROQ_API_KEY,
    DEFAULT_MODEL,
)

client = Groq(
    api_key=GROQ_API_KEY
)

# ==========================================================
# RETRY / RATE LIMIT HANDLING
# ==========================================================

MAX_RETRIES = 5
BASE_DELAY_SECONDS = 2.0

_WAIT_HINT_PATTERN = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)

T = TypeVar("T")


def _seconds_until_retry(exc: Exception, attempt: int) -> float:
    """
    Prefer Groq's own hint about when to retry (Retry-After header, or the
    "try again in Xs" text in the error message) over a guess.
    """
    response = getattr(exc, "response", None)
    if response is not None:
        header = response.headers.get("retry-after")
        if header:
            try:
                return float(header)
            except ValueError:
                pass

    match = _WAIT_HINT_PATTERN.search(str(exc))
    if match:
        return float(match.group(1))

    return BASE_DELAY_SECONDS * (2 ** attempt)


def call_with_retry(request_fn: Callable[[], T], max_retries: int = MAX_RETRIES) -> T:
    """
    Call a Groq API request, retrying on rate limits (429), server-side
    capacity/outage errors (5xx), and transient connection errors with
    backoff instead of letting them crash the caller.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            return request_fn()
        except RateLimitError as exc:
            last_exc = exc
            delay = _seconds_until_retry(exc, attempt)
            print(
                f"[Groq] Rate limit hit. Waiting {delay:.1f}s "
                f"(attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(delay)
        except InternalServerError as exc:
            last_exc = exc
            delay = _seconds_until_retry(exc, attempt)
            print(
                f"[Groq] Server error (model over capacity / outage). "
                f"Waiting {delay:.1f}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(delay)
        except APIConnectionError as exc:
            last_exc = exc
            delay = BASE_DELAY_SECONDS * (2 ** attempt)
            print(
                f"[Groq] Connection error. Waiting {delay:.1f}s "
                f"(attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(delay)

    raise last_exc


# ==========================================================
# REASONING MODELS (Qwen3, etc.)
# ==========================================================
# Qwen3 is a "thinking" model: unlike Llama, it silently generates a whole
# hidden <think>...</think> chain-of-thought before its real answer. Those
# tokens count against both max_completion_tokens (can truncate the JSON
# before it's written) and Groq's per-minute token rate limit. Requesting
# reasoning_effort="none" tells Qwen to skip that step. Fall back to no
# reasoning param at all if the model/account rejects it.

def _is_reasoning_model(model: str) -> bool:
    return "qwen" in model.lower()


def create_chat_completion(*, model: str, disable_reasoning: bool = True, **kwargs):
    """
    Wrapper around client.chat.completions.create with automatic retry on
    rate limits/connection errors, and an attempt to turn off Qwen's hidden
    reasoning tokens (safe no-op for non-Qwen models).
    """

    def _do(with_reasoning_off: bool):
        params = dict(kwargs, model=model)
        if with_reasoning_off:
            params["reasoning_effort"] = "none"
        return client.chat.completions.create(**params)

    if disable_reasoning and _is_reasoning_model(model):
        try:
            return call_with_retry(lambda: _do(True))
        except BadRequestError as exc:
            print(f"[Groq] {model} rejected reasoning_effort ({exc}); retrying without it.")

    return call_with_retry(lambda: _do(False))


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
    Generic Groq Chat Client. Retries automatically on rate limits.

    Extra parameters are accepted for compatibility
    with the old Ollama client.
    """

    response = create_chat_completion(
        model=model or DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_completion_tokens=num_predict,
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