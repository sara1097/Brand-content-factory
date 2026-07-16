"""
Client for the deployed WanGP FastAPI wrapper (running on Modal).

Talks to the existing, unmodified wangp_api service purely over HTTP:

    POST /generate       submit a text-to-video / image-to-video job
    GET  /job/{id}       poll status/progress
    GET  /job/{id}/file  download a finished output file

Nothing in wangp_api or Wan2GP is touched by this module -- it only calls
the deployed API's public HTTP endpoints (see wangp_api/README.md).

Any generation setting beyond prompt/seed/image_refs (resolution, steps,
video_prompt_type, etc.) is intentionally left unset here and comes from
the settings template already configured inside the wangp_api project
(wangp_api/settings_templates/*.json) -- adjust it there, not here.
"""
from __future__ import annotations

import base64
import mimetypes
import os
import random
import time
from pathlib import Path

import requests

from config import (
    WANGP_API_URL,
    WANGP_DOWNLOAD_TIMEOUT_SECONDS,
    WANGP_LOG_EVERY_N_POLLS,
    WANGP_MAX_WAIT_SECONDS,
    WANGP_POLL_HTTP_TIMEOUT_SECONDS,
    WANGP_POLL_INTERVAL_SECONDS,
    WANGP_SUBMIT_TIMEOUT_SECONDS,
)

TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}

# A short, capped log file mirroring the request/progress lines printed to
# the terminal below -- so there's always a small, shareable/downloadable
# file of "what requests were made" instead of nothing, and instead of an
# ever-growing file. Oldest lines are dropped once _MAX_LOG_LINES is hit.
_LOG_FILE = Path("outputs") / "wangp_requests.log"
_MAX_LOG_LINES = 200


def _log(message: str) -> None:
    """Print a line to the terminal and append it to outputs/wangp_requests.log
    (capped at _MAX_LOG_LINES so the log file stays small)."""
    print(message)
    try:
        _LOG_FILE.parent.mkdir(exist_ok=True)
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
        lines = _LOG_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > _MAX_LOG_LINES:
            _LOG_FILE.write_text("\n".join(lines[-_MAX_LOG_LINES:]) + "\n", encoding="utf-8")
    except OSError:
        pass  # logging must never break generation


class WanGPClientError(Exception):
    """Raised on any failure talking to the deployed WanGP API."""


def _image_to_data_uri(image_path: str) -> str:
    """Reads a local image and encodes it as a base64 data: URI, which
    wangp_api's media resolver (app/media.py) accepts directly for
    image_refs / image_start -- the Modal container can't see the local
    filesystem, so the photo has to travel inside the request body."""
    path = Path(image_path)
    if not path.is_file():
        raise WanGPClientError(f"Image not found: {image_path}")

    mime, _ = mimetypes.guess_type(path.name)
    mime = mime or "image/jpeg"

    with path.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime};base64,{b64}"


def _submit_job(prompt: str, image_path: str | None, seed: int) -> str:
    payload: dict = {
        "prompt": prompt,
        "seed": seed,
    }

    if image_path:
        # Reference image: keeps the product's exact packaging/branding
        # while animating around it (matches the LTX-2 MSR default
        # template already configured in wangp_api).
        payload["image_refs"] = [_image_to_data_uri(image_path)]

    # No other settings are set here on purpose -- the deployed template
    # in wangp_api/settings_templates/*.json supplies everything else
    # (including the no-photo / text-only behaviour).

    prompt_preview = prompt if len(prompt) <= 80 else prompt[:77] + "..."
    _log(f"[WanGP] -> POST /generate  seed={seed}  image_ref={'yes' if image_path else 'no'}  prompt=\"{prompt_preview}\"")

    try:
        # Generous timeout: if the Modal container is cold (scaled to
        # zero), this single request has to wait for the platform to spin
        # it up and finish WanGP session init before it even gets a
        # response -- that can take minutes, not seconds.
        response = requests.post(
            f"{WANGP_API_URL}/generate", json=payload, timeout=WANGP_SUBMIT_TIMEOUT_SECONDS
        )
    except requests.exceptions.Timeout as exc:
        raise WanGPClientError(
            f"WanGP /generate timed out after {WANGP_SUBMIT_TIMEOUT_SECONDS:.0f}s. "
            "This usually means the Modal container was cold-starting (loading the "
            "model into GPU memory) and needs longer, or it's stuck -- check "
            f"{WANGP_API_URL}/health and the Modal app logs. You can also raise "
            "WANGP_SUBMIT_TIMEOUT_SECONDS in .env, or set min_containers=1 in "
            "modal_app.py to avoid cold starts entirely."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise WanGPClientError(
            f"Could not reach WanGP API at {WANGP_API_URL}: {exc}"
        ) from exc

    if response.status_code not in (200, 202):
        raise WanGPClientError(
            f"WanGP /generate failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    job_id = data.get("id")
    if not job_id:
        raise WanGPClientError(f"WanGP /generate response missing job id: {data}")

    _log(f"[WanGP] <- job accepted  job_id={job_id}")
    return job_id


def _wait_for_job(
    job_id: str,
    label: str = "",
    on_progress=None,
    variant: int = 1,
    total_variants: int = 1,
) -> dict:
    """
    on_progress, if given, is called as on_progress(variant, total_variants,
    pct, status, phase) every time we get a fresh reading -- pct is 0-100
    or None if the API hasn't reported one yet. Used by callers (e.g. a
    Streamlit app) to drive a live progress bar; must not raise.
    """
    deadline = time.time() + WANGP_MAX_WAIT_SECONDS
    poll_count = 0
    last_logged_pct = None
    max_pct_seen = 0

    def _notify(pct, status, phase):
        if on_progress is None:
            return
        try:
            on_progress(variant, total_variants, pct, status, phase)
        except Exception:
            pass  # a broken UI callback must never break generation

    _notify(0, "queued", None)

    while time.time() < deadline:
        poll_count += 1
        try:
            response = requests.get(
                f"{WANGP_API_URL}/job/{job_id}", timeout=WANGP_POLL_HTTP_TIMEOUT_SECONDS
            )
        except requests.exceptions.RequestException as exc:
            raise WanGPClientError(f"WanGP /job/{job_id} request failed: {exc}") from exc

        if response.status_code != 200:
            raise WanGPClientError(
                f"WanGP /job/{job_id} failed ({response.status_code}): {response.text}"
            )

        job = response.json()
        status = job.get("status")
        progress = job.get("progress") or {}
        pct = progress.get("progress")
        phase = progress.get("phase")

        current_step = progress.get("current_step")
        total_steps = progress.get("total_steps")

        if pct is not None:
            if current_step and total_steps and total_steps > 0:
                pct = int(((current_step - 1) * 100 + pct) / total_steps)
            max_pct_seen = max(max_pct_seen, pct)
            pct = max_pct_seen

        _notify(pct, status, phase)

        # We still POLL every WANGP_POLL_INTERVAL_SECONDS (needed to catch
        # completion promptly), but only PRINT/LOG a line on the first
        # poll, every Nth poll, or when the percentage actually moved --
        # this is what turns "silent + hundreds of requests" into
        # "visible progress + a handful of log lines".
        if poll_count == 1 or poll_count % WANGP_LOG_EVERY_N_POLLS == 0 or pct != last_logged_pct:
            _log(
                f"[WanGP]{label} <- GET /job/{job_id[:8]}  poll #{poll_count}  "
                f"status={status}  progress={pct if pct is not None else '?'}%  "
                f"phase={phase or '-'}"
            )
            last_logged_pct = pct

        if status in TERMINAL_STATUSES:
            _log(f"[WanGP]{label} job {job_id[:8]} finished: status={status} (after {poll_count} polls)")
            _notify(100 if status == "succeeded" else pct, status, phase)
            return job

        time.sleep(WANGP_POLL_INTERVAL_SECONDS)

    raise WanGPClientError(f"WanGP job {job_id} timed out after {WANGP_MAX_WAIT_SECONDS}s")


def _download_output(job_id: str, output_dir: str, index: int = 0) -> str:
    try:
        response = requests.get(
            f"{WANGP_API_URL}/job/{job_id}/file",
            params={"index": index},
            timeout=WANGP_DOWNLOAD_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as exc:
        raise WanGPClientError(f"WanGP /job/{job_id}/file request failed: {exc}") from exc

    if response.status_code != 200:
        raise WanGPClientError(
            f"WanGP /job/{job_id}/file failed ({response.status_code}): {response.text}"
        )

    os.makedirs(output_dir, exist_ok=True)
    dest = Path(output_dir) / f"{job_id}.mp4"
    dest.write_bytes(response.content)
    return str(dest)


def generate_video_variants(
    prompts: list[str],
    image_path: str | None = None,
    output_dir: str = "outputs",
    on_progress=None,
) -> list[dict]:
    """
    Submits ONE WanGP job per prompt in `prompts` -- e.g. two different
    prompts produce two different videos, each one continuous single
    shot. This is NOT the same prompt reused with different seeds; each
    job renders its own distinct prompt (with its own random seed). Waits
    for all jobs, downloads the finished MP4s locally, and returns
    per-variant metadata.

    on_progress, if given, is called as on_progress(variant, total_variants,
    pct, status, phase) each time fresh progress is available for any
    variant -- pass this to drive a UI progress bar (e.g. in Streamlit).

    Returns a list of dicts like:
        {"variant": 1, "prompt": "...", "seed": 123, "job_id": "...",
         "status": "succeeded", "video_path": "outputs/<job_id>.mp4"}
    or, on failure for that variant:
        {"variant": 2, "prompt": "...", "seed": 124, "job_id": "...",
         "status": "failed", "error": "..."}
    """
    _log(f"\n[WanGP] === {len(prompts)} video prompt(s) to render ===")
    for i, prompt in enumerate(prompts, start=1):
        _log(f"[WanGP] Prompt {i}: {prompt}")
    _log("[WanGP] " + "=" * 40)

    submitted = []
    for i, prompt in enumerate(prompts):
        seed = random.randint(0, 2_000_000_000)
        _log(f"[WanGP] Submitting variant {i + 1}/{len(prompts)} (seed={seed})...")
        job_id = _submit_job(prompt=prompt, image_path=image_path, seed=seed)
        submitted.append({"variant": i + 1, "prompt": prompt, "seed": seed, "job_id": job_id})

    variants = []
    for item in submitted:
        label = f" [variant {item['variant']}]"
        try:
            job = _wait_for_job(
                item["job_id"],
                label=label,
                on_progress=on_progress,
                variant=item["variant"],
                total_variants=len(prompts),
            )
        except WanGPClientError as exc:
            variants.append({**item, "status": "error", "error": str(exc)})
            continue

        status = job.get("status")
        if status != "succeeded" or not job.get("generated_files"):
            error_detail = job.get("error_message") or "; ".join(
                e.get("message", "") for e in job.get("errors", [])
            )
            variants.append({**item, "status": status, "error": error_detail or "Unknown error"})
            continue

        try:
            local_path = _download_output(item["job_id"], output_dir)
        except WanGPClientError as exc:
            variants.append({**item, "status": "error", "error": str(exc)})
            continue

        variants.append(
            {
                **item,
                "status": "succeeded",
                "video_path": local_path,
                "generated_files": job.get("generated_files"),
            }
        )

    return variants