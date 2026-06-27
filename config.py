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
# Ollama
# ==========================================================

OLLAMA_URL = "http://localhost:11434"

OLLAMA_MODEL = "qwen3.5:4b"

# ==========================================================
# Groq
# ==========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = "llama-3.3-70b-versatile"

# ==========================================================
# Default model (Groq)
# ==========================================================

MODEL = GROQ_MODEL

TIMEOUT = 900

# ==========================================================
# Chroma
# ==========================================================

COLLECTION_NAME = "product_research"

EMBEDDING_MODEL = "nomic-embed-text"