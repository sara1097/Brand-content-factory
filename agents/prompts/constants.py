"""
constants.py

Shared constants used across all AI agents.

Version: 1.0.0
"""

# ============================================================
# PROJECT INFORMATION
# ============================================================

PLATFORM_NAME = "AI Marketing Intelligence Platform"

PROMPT_VERSION = "1.0.0"

AUTHOR = "khaled mohsen"

# ============================================================
# LLM DEFAULT SETTINGS
# ============================================================

DEFAULT_LLM_SETTINGS = {

    "temperature": 0.3,

    "top_p": 0.9,

    "top_k": 40,

    "repeat_penalty": 1.1,

    "num_ctx": 8192,

    "num_predict": 1500

}

# ============================================================
# AGENT SETTINGS
# ============================================================

AGENT_SETTINGS = {

    "product": {

        "temperature": 0.20,

        "top_p": 0.90,

        "top_k": 40,

        "repeat_penalty": 1.10,

        "num_ctx": 8192,

        "num_predict": 1500

    },

    "research": {

        "temperature": 0.30,

        "top_p": 0.95,

        "top_k": 50,

        "repeat_penalty": 1.05,

        "num_ctx": 8192,

        "num_predict": 4000

    },

    "comparison": {

        "temperature": 0.25,

        "top_p": 0.95,

        "top_k": 50,

        "repeat_penalty": 1.05,

        "num_ctx": 8192,

        "num_predict": 1800

    },

    "marketing": {
    "temperature": 0.35,
    "top_p": 0.90,
    "top_k": 40,
    "repeat_penalty": 1.05,
    "num_ctx": 8192,
    "num_predict": 1200
},
"variant": {

    "temperature": 0.50,

    "top_p": 0.90,

    "top_k": 40,

    "repeat_penalty": 1.05,

    "num_ctx": 8192,

    "num_predict": 1800

},
"compliance": {

    "temperature": 0.10,

    "top_p": 0.90,

    "top_k": 40,

    "repeat_penalty": 1.05,

    "num_ctx": 8192,

    "num_predict": 2000

},

    "report": {

        "temperature": 0.35,

        "top_p": 0.95,

        "top_k": 50,

        "repeat_penalty": 1.05,

        "num_ctx": 8192,

        "num_predict": 3500

    }

}

# ============================================================
# CONFIDENCE LEVELS
# ============================================================

CONFIDENCE = {

    "VERY_LOW": 0.20,

    "LOW": 0.40,

    "MEDIUM": 0.60,

    "HIGH": 0.80,

    "VERY_HIGH": 0.95

}

# ============================================================
# OUTPUT MODES
# ============================================================

OUTPUT_MODE = {

    "JSON": "json",

    "TEXT": "text"

}

# ============================================================
# SUPPORTED INPUTS
# ============================================================

SUPPORTED_INPUTS = [

    "image",

    "text",

    "image+text"

]

# ============================================================
# RETRY SETTINGS
# ============================================================

MAX_JSON_RETRIES = 2

JSON_REPAIR_TEMPERATURE = 0.15

# ============================================================
# PIPELINE INFORMATION
# ============================================================

PIPELINE = [

    "product",

    "research",

    "comparison",

    "marketing",

    "variant",

    "report"

]