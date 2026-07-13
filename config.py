"""Central configuration"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# Project paths
# ==========================================================

PROJECT_ROOT = Path(__file__).parent

DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
OUTPUTS_DIR = DATA_DIR / "outputs"

DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# ==========================================================
# Groq
# ==========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PRODUCT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

DEFAULT_MODEL = "llama-3.3-70b-versatile"

MODEL = DEFAULT_MODEL

TIMEOUT = 900

 
# ==========================================================
# Qwen (prompt enhancement)
# ==========================================================
# Groq-hosted Qwen model used ONLY where explicitly passed as model=... --
# e.g. agents/prompt_agent.py::generate_video_prompts(). It is NOT the
# default for models/llm.py::ask_qwen() (that default stays config.MODEL,
# unchanged, so other agents/features that call ask_qwen() without an
# explicit model= are unaffected).
 
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen/qwen3-32b")
 
# ==========================================================
# WanGP Video Generation API (deployed on Modal)
# ==========================================================
# Base URL of the deployed wangp_api FastAPI wrapper (see the "modal_app.py"
# deployment). Do not include a trailing slash.
#
# NOTE: any WanGP generation settings beyond prompt/seed/image_refs (e.g.
# resolution, steps, video_prompt_type for the no-photo case, etc.) are
# intentionally NOT guessed or overridden here -- they come from the
# settings template already configured inside the wangp_api project
# (wangp_api/settings_templates/*.json). Adjust settings there, not here.
 
WANGP_API_URL = os.getenv(
    "WANGP_API_URL",
    "https://sagdafathy--wangp-api-fastapi-app.modal.run",
).rstrip("/")

# Feature toggle: set ENABLE_VIDEO_GENERATION=false in .env to skip the
# WanGP video node entirely (renders take ~10 min and hit the Modal GPU,
# so turn this off for fast/cheap test runs). The sidebar checkbox in
# app_qwen.py defaults to this value and can override it per run.
ENABLE_VIDEO_GENERATION = (
    os.getenv("ENABLE_VIDEO_GENERATION", "true").strip().lower()
    not in {"0", "false", "no", "off"}
)
 
# Number of distinct video prompts/videos to generate per request. The
# two prompts are different creative directions for the same product, not
# the same prompt reused with different seeds.
WANGP_NUM_VARIANTS = int(os.getenv("WANGP_NUM_VARIANTS", "2"))
  
# How long to wait for the INITIAL POST /generate call to return a job id.
# This has to be generous: if the Modal container has scaled down to zero
# (idle), the platform has to cold-start it -- pull the image, initialize
# the WanGP session, and load the model into GPU memory -- before it can
# even accept the request. That routinely takes minutes, not seconds, on
# the first request after idle. A 60s timeout here is what produced
# "Read timed out (read timeout=60)". Subsequent requests against an
# already-warm container return almost immediately.
WANGP_SUBMIT_TIMEOUT_SECONDS = float(os.getenv("WANGP_SUBMIT_TIMEOUT_SECONDS", "900"))
 
# Timeout for each individual GET /job/{id} poll request (the container is
# already warm by this point, so this can stay short).
WANGP_POLL_HTTP_TIMEOUT_SECONDS = float(os.getenv("WANGP_POLL_HTTP_TIMEOUT_SECONDS", "60"))
 
# Timeout for downloading the finished video file.
WANGP_DOWNLOAD_TIMEOUT_SECONDS = float(os.getenv("WANGP_DOWNLOAD_TIMEOUT_SECONDS", "180"))
 
# Polling cadence / ceiling while waiting for a WanGP job to finish.
# NOTE: this was 3s, which on a ~5min render means ~100 GET /job/{id}
# requests PER VIDEO (200+ for the two variants combined) -- that's the
# "too many requests" cost problem. 10s cuts that by ~3x while still
# feeling responsive.
WANGP_POLL_INTERVAL_SECONDS = float(os.getenv("WANGP_POLL_INTERVAL_SECONDS", "10"))
WANGP_MAX_WAIT_SECONDS = float(os.getenv("WANGP_MAX_WAIT_SECONDS", "900"))

# How many poll cycles between terminal/log progress lines. We still poll
# the API every WANGP_POLL_INTERVAL_SECONDS (needed to know when the job
# is done), but we only PRINT a line every Nth poll (or when the reported
# percentage changes), so the terminal shows steady progress instead of
# either total silence or a flood of near-duplicate lines.
WANGP_LOG_EVERY_N_POLLS = int(os.getenv("WANGP_LOG_EVERY_N_POLLS", "3"))
 
# ==========================================================
# Magic Hour Image Generation API
# ==========================================================
# Used by tools/magichour_client.py for the 4 image-day posts of the
# 7-day calendar (text prompt + product reference image -> image).

MAGICHOUR_API_KEY = os.getenv("MAGICHOUR_API_KEY")

MAGICHOUR_API_URL = os.getenv("MAGICHOUR_API_URL", "https://api.magichour.ai").rstrip("/")

# Polling cadence / ceiling while waiting for a Magic Hour image job.
MAGICHOUR_POLL_INTERVAL_SECONDS = float(os.getenv("MAGICHOUR_POLL_INTERVAL_SECONDS", "5"))
MAGICHOUR_MAX_WAIT_SECONDS = float(os.getenv("MAGICHOUR_MAX_WAIT_SECONDS", "600"))
MAGICHOUR_HTTP_TIMEOUT_SECONDS = float(os.getenv("MAGICHOUR_HTTP_TIMEOUT_SECONDS", "60"))

# ==========================================================
# Product image auto-sourcing (web scrape + vision validation)
# ==========================================================
# When the user runs the pipeline without uploading a product photo, we
# search the web for candidate images and let the vision model confirm
# one matches the description before using it as the reference image.

# How many scraped candidate images to try before giving up.
IMAGE_SCRAPE_MAX_CANDIDATES = int(os.getenv("IMAGE_SCRAPE_MAX_CANDIDATES", "5"))

# Minimum confidence (0-1) the vision validator must report for a
# scraped image to be accepted as the product reference image.
IMAGE_MATCH_MIN_CONFIDENCE = float(os.getenv("IMAGE_MATCH_MIN_CONFIDENCE", "0.6"))

# ==========================================================
# 7-day content calendar media mix
# ==========================================================
# Fixed per-week media plan: 2 video days + 4 image days + 1 text-only
# day = 7 posts. Video days map onto the WANGP_NUM_VARIANTS videos and
# image days are rendered through Magic Hour.
MEDIA_MIX = {"video": 2, "image": 4, "text": 1}

# ==========================================================
# Chroma
# ==========================================================

COLLECTION_NAME = "product_research"

EMBEDDING_MODEL = "nomic-embed-text"