"""
Client for the Magic Hour image generation API (https://magichour.ai).

Used to render the image-day posts of the 7-day content calendar:
text prompt + (optional) product reference image -> one PNG/JPEG.

Endpoints used (see https://docs.magichour.ai/api-reference):

    POST /v1/files/upload-urls        get a pre-signed URL, then PUT the
                                      reference image bytes to it
    POST /v1/ai-image-editor          text + reference image -> image
    POST /v1/ai-image-generator       text only -> image (fallback when
                                      no reference image is available)
    GET  /v1/image-projects/{id}      poll status; `downloads` appears
                                      once status == "complete"

Auth: `Authorization: Bearer <MAGICHOUR_API_KEY>` from .env.
"""
from __future__ import annotations

import time
from pathlib import Path

import requests

from config import (
    MAGICHOUR_API_KEY,
    MAGICHOUR_API_URL,
    MAGICHOUR_HTTP_TIMEOUT_SECONDS,
    MAGICHOUR_MAX_WAIT_SECONDS,
    MAGICHOUR_POLL_INTERVAL_SECONDS,
)

TERMINAL_STATUSES = {"complete", "error", "canceled"}


class MagicHourClientError(Exception):
    """Raised on any failure talking to the Magic Hour API."""


def _headers() -> dict:
    if not MAGICHOUR_API_KEY or MAGICHOUR_API_KEY == "your-magic-hour-api-key-here":
        raise MagicHourClientError(
            "MAGICHOUR_API_KEY is not set. Add it to the .env file in the "
            "project root (get a key from the Magic Hour Developer Hub)."
        )
    return {"Authorization": f"Bearer {MAGICHOUR_API_KEY}"}


def _request(method: str, path: str, **kwargs) -> dict:
    """One authenticated JSON request with normalized error reporting."""
    url = f"{MAGICHOUR_API_URL}{path}"
    try:
        response = requests.request(
            method, url, headers=_headers(),
            timeout=MAGICHOUR_HTTP_TIMEOUT_SECONDS, **kwargs,
        )
    except requests.exceptions.RequestException as exc:
        raise MagicHourClientError(f"Magic Hour {method} {path} failed: {exc}") from exc

    if response.status_code == 402:
        raise MagicHourClientError(
            "Magic Hour says the account is out of credits (402). "
            "Top up at magichour.ai to keep generating images."
        )
    if response.status_code not in (200, 201, 202):
        raise MagicHourClientError(
            f"Magic Hour {method} {path} failed "
            f"({response.status_code}): {response.text[:300]}"
        )
    return response.json()


def upload_reference_image(image_path: str) -> str:
    """
    Upload a local image to Magic Hour storage and return its `file_path`
    (e.g. "api-assets/<id>/<file>.jpg") for use in generation requests.
    Upload once per pipeline run and reuse the path for all image days.
    """
    path = Path(image_path)
    if not path.is_file():
        raise MagicHourClientError(f"Reference image not found: {image_path}")

    extension = path.suffix.lstrip(".").lower() or "jpg"
    if extension == "jpeg":
        extension = "jpg"

    data = _request(
        "POST", "/v1/files/upload-urls",
        json={"items": [{"type": "image", "extension": extension}]},
    )
    try:
        item = data["items"][0]
        upload_url, file_path = item["upload_url"], item["file_path"]
    except (KeyError, IndexError) as exc:
        raise MagicHourClientError(f"Unexpected upload-urls response: {data}") from exc

    try:
        put = requests.put(
            upload_url, data=path.read_bytes(),
            timeout=MAGICHOUR_HTTP_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as exc:
        raise MagicHourClientError(f"Reference image upload failed: {exc}") from exc
    if put.status_code not in (200, 201):
        raise MagicHourClientError(
            f"Reference image upload failed ({put.status_code}): {put.text[:300]}"
        )

    print(f"[MagicHour] Reference image uploaded -> {file_path}")
    return file_path


def _submit_image_job(
    prompt: str,
    reference_file_path: str | None,
    name: str,
    aspect_ratio: str,
) -> dict:
    """Submit one generation job; returns {"id": ..., "credits_charged": ...}."""
    if reference_file_path:
        payload = {
            "name": name,
            "image_count": 1,
            "aspect_ratio": aspect_ratio,
            "style": {"prompt": prompt},
            "assets": {"image_file_paths": [reference_file_path]},
        }
        endpoint = "/v1/ai-image-editor"
    else:
        payload = {
            "name": name,
            "image_count": 1,
            "aspect_ratio": aspect_ratio,
            "style": {"prompt": prompt, "tool": "ai-photo-generator"},
        }
        endpoint = "/v1/ai-image-generator"

    prompt_preview = prompt if len(prompt) <= 80 else prompt[:77] + "..."
    print(
        f"[MagicHour] -> POST {endpoint}  "
        f"reference={'yes' if reference_file_path else 'no'}  prompt=\"{prompt_preview}\""
    )
    data = _request("POST", endpoint, json=payload)
    if not data.get("id"):
        raise MagicHourClientError(f"Magic Hour response missing project id: {data}")
    print(f"[MagicHour] <- job accepted  id={data['id']}  credits={data.get('credits_charged')}")
    return data


def _wait_for_image(project_id: str) -> dict:
    deadline = time.time() + MAGICHOUR_MAX_WAIT_SECONDS
    while time.time() < deadline:
        job = _request("GET", f"/v1/image-projects/{project_id}")
        status = job.get("status")
        if status in TERMINAL_STATUSES:
            print(f"[MagicHour] job {project_id} finished: status={status}")
            return job
        time.sleep(MAGICHOUR_POLL_INTERVAL_SECONDS)
    raise MagicHourClientError(
        f"Magic Hour job {project_id} timed out after {MAGICHOUR_MAX_WAIT_SECONDS:.0f}s"
    )


def _download_image(url: str, dest: Path) -> str:
    try:
        response = requests.get(url, timeout=MAGICHOUR_HTTP_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as exc:
        raise MagicHourClientError(f"Image download failed: {exc}") from exc
    if response.status_code != 200:
        raise MagicHourClientError(f"Image download failed ({response.status_code})")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(response.content)
    return str(dest)


def generate_image(
    prompt: str,
    reference_file_path: str | None = None,
    fallback_prompt: str | None = None,
    output_dir: str = "outputs/images",
    name: str = "Brand post image",
    aspect_ratio: str = "1:1",
) -> dict:
    """
    Render ONE image and download it locally.

    `reference_file_path` is a Magic Hour storage path from
    `upload_reference_image()` (upload once, reuse for every post) --
    when given, the AI Image Editor keeps the product's real look while
    restyling it per the prompt; when None, plain text-to-image is used.

    `fallback_prompt`, if given, is used INSTEAD of `prompt` when the
    editor submission fails and the job is retried as text-to-image --
    pass a version enriched with a concrete product description, since
    the text-only model can't see the reference photo.

    Returns:
        {"status": "succeeded", "image_path": "outputs/images/<id>.png",
         "id": ..., "credits_charged": ..., "reference_used": ..., "prompt": ...}
    or  {"status": "failed", "error": "...", "prompt": ...}     (never raises)
    """
    try:
        used_reference = bool(reference_file_path)
        try:
            submitted = _submit_image_job(prompt, reference_file_path, name, aspect_ratio)
        except MagicHourClientError as exc:
            if not reference_file_path:
                raise
            # The AI Image Editor costs more credits per image than the
            # plain generator and can 402 while the generator still
            # works. A failed submission charges nothing, so retry as
            # plain text-to-image (with the enriched fallback prompt)
            # instead of failing the whole post.
            print(f"[MagicHour] Editor submission failed ({exc}); retrying without reference image.")
            prompt = fallback_prompt or prompt
            submitted = _submit_image_job(prompt, None, name, aspect_ratio)
            used_reference = False

        job = _wait_for_image(submitted["id"])

        if job.get("status") != "complete":
            error = (job.get("error") or {}).get("message") or f"status={job.get('status')}"
            return {"status": "failed", "error": error, "prompt": prompt}

        downloads = job.get("downloads") or []
        if not downloads:
            return {"status": "failed", "error": "No downloads in completed job", "prompt": prompt}

        url = downloads[0]["url"]
        suffix = ".png" if ".png" in url.lower() else ".jpg"
        dest = Path(output_dir) / f"{submitted['id']}{suffix}"
        local_path = _download_image(url, dest)

        return {
            "status": "succeeded",
            "image_path": local_path,
            "id": submitted["id"],
            "credits_charged": submitted.get("credits_charged"),
            "reference_used": used_reference,
            "prompt": prompt,
        }
    except MagicHourClientError as exc:
        return {"status": "failed", "error": str(exc), "prompt": prompt}
    except Exception as exc:
        return {"status": "failed", "error": f"Unexpected error: {exc}", "prompt": prompt}
