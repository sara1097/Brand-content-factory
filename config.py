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
WANGP_POLL_INTERVAL_SECONDS = float(os.getenv("WANGP_POLL_INTERVAL_SECONDS", "3"))
WANGP_MAX_WAIT_SECONDS = float(os.getenv("WANGP_MAX_WAIT_SECONDS", "900"))
 
# ==========================================================
# Chroma
# ==========================================================

COLLECTION_NAME = "product_research"

EMBEDDING_MODEL = "nomic-embed-text"