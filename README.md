# 📊 Brand Content Factory — Enterprise AI Marketing Intelligence Platform (Qwen Edition) 

An end-to-end **multi-agent AI pipeline** that turns a plain product description (plus an optional product image) into a complete, ready-to-use marketing package: product intelligence, live market research, a full marketing strategy, a **7-day content calendar with the media already generated** (2 AI videos + 4 AI images + 1 text-only post), ad copy variants, a compliance review, and an exportable executive report (PDF / JSON / TXT).

**No product photo? No problem.** If you don't upload one, the pipeline web-scrapes candidate product images, has the vision model confirm one actually matches your description, and uses it as the reference image for both video and image generation.

Built with **Python + Streamlit**, orchestrated with **LangGraph**, powered by **Groq cloud LLMs** (Qwen 3 32B for text, Llama vision for images), a deployed **WanGP video-generation API**, and the **Magic Hour image-generation API**.

---

## ⚡ Quick Start

> 🟢 **The project is fully portable — no matter where you place or clone this folder, just create a fresh Python environment inside it and run.** Requires **Python 3.11+** ([download](https://www.python.org/downloads/)).

### Windows (PowerShell / CMD)
```powershell
# 1. From the project root, create and activate a fresh environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Groq API key (free at https://console.groq.com)
copy .env.example .env      # then put your key in .env  ->  GROQ_API_KEY=gsk_...

# 4. Launch the app
streamlit run app_qwen.py
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your key in .env  ->  GROQ_API_KEY=gsk_...
streamlit run app_qwen.py
```

### Docker (no local Python needed)
```bash
docker build -t brand-factory .
docker run -p 8501:8501 --env-file .env brand-factory
```

The app opens at `http://localhost:8501`. Enter a product description, optionally upload a product photo, choose the business constraints in the sidebar, and press **🚀 Run Full Pipeline**.

> ⚠️ **Do not reuse an environment folder that was created on another machine or in another location** (e.g. a copied `venv`/`INSTRUCTOR_ENV`). Python environments hard-code the absolute path they were created at, so their `streamlit.exe` / `pip.exe` launchers break as soon as the folder moves. Always create your own environment with the steps above — it takes one minute. If you must run a bundled environment, call modules through its interpreter directly (`.\INSTRUCTOR_ENV\python.exe -m streamlit run app_qwen.py`), which works regardless of location.

---

## 🧠 What the pipeline does

One button runs a **LangGraph pipeline of 11 AI nodes** — a sequential analysis chain, then a parallel fan-out for media generation — each rendered live as a collapsible card with a real-time status dashboard:

| # | Node | Agent | What it produces |
|---|------|-------|------------------|
| 1 | 🔎 Image Sourcing | `image_validator_agent` + `tools/image_scraper` | Product reference image: your upload, or a web-scraped image **validated by the vision model** against your description |
| 2 | 📦 Product Intelligence | `product_agent` + `vision_agent` | Structured product attributes from text **and image** (Llama vision) |
| 3 | 🌍 Market Intelligence | `research_agent` + live web search (`ddgs`) | Price landscape, competitors, verifiable source evidence |
| 4 | 📢 Marketing Strategy | `marketing_strategy_agent` | Positioning, channels, budget split, KPIs — tailored to country/budget/goal |
| 5 | 📅 Content Calendar | `content_agent` | 7-day posting plan with an enforced media mix: **2 video / 4 image / 1 text-only days** |
| 6 | 🎯 Marketing Variants | `variant_agent` | Multiple ad-copy variants scored for fit |
| 7 | 🛡️ Compliance Review | `compliance_agent` | Regulatory / claims risk check of the copy |
| 8 | 🎬 AI Videos | `video_agent` + `prompt_agent` | 2 promo videos (WanGP on Modal) — one per **video day** of the calendar |
| 9 | 🖼️ AI Post Images | `image_agent` + `tools/magichour_client` | 4 post images (Magic Hour, reference-image + prompt) — one per **image day** |
| 10 | 🗓️ Final 7-Day Plan | `graph/nodes.assemble_calendar_node` | The deliverable: 7 posts, each with caption/hashtags/CTA **and its generated media attached** |
| 11 | 📄 Executive Report | `report_agent` | Narrative executive report → export as **PDF**, JSON, or TXT |

Nodes 8 and 9 run **in parallel** (separate render services); node 6→7 runs alongside them. Everything joins into the final plan and report.

**Fault-tolerant by design:** every node stores a `node_error` instead of raising — if one fails (rate limit, API outage), the dashboard marks it ❌ and the pipeline continues with the remaining nodes.

**Rate-limit engineering:** all Qwen calls use tuned token budgets (`num_predict` / `max_completion_tokens`) to stay under Groq's measured 6000 tokens-per-minute ceiling — see the constants at the top of `app_qwen.py`.

---

## 📁 Project structure

```
├── app_qwen.py            ← main Streamlit app (entry point)
├── config.py              ← models, API keys, global settings, media mix
├── graph/                 ← LangGraph orchestration
│   ├── state.py           ← shared PipelineState (one key per node)
│   ├── nodes.py           ← fault-tolerant node wrappers + token budgets
│   └── builder.py         ← graph wiring (sequential chain + media fan-out)
├── agents/                ← one agent per pipeline node
│   ├── base_agent.py      ← shared LLM-call + JSON-validation logic
│   ├── image_validator_agent.py ← scraped-image vision check + acquisition
│   ├── image_agent.py     ← Magic Hour images for the calendar's image days
│   └── prompts/           ← versioned system prompts + JSON schemas
├── core/validator.py      ← output schema validation & reliability scoring
├── tools/                 ← Groq client (retry/backoff), vision client, web search,
│                            image scraper (ddgs), Magic Hour client
├── models/                ← Qwen text helper + WanGP video API client
├── reports/               ← ReportLab PDF generation (styles/components/generator)
├── schemas/               ← Pydantic models for video prompt generation
├── utils/json_parser.py   ← robust JSON extraction from LLM output
├── tests/ + test_*.py     ← pytest suite (validator, profitability, media mix, assembly)
├── Dockerfile             ← containerized deployment
└── DOCUMENTATION.md       ← full technical documentation
```

---

## 🧪 Running the tests

With your environment activated (see Quick Start):

```powershell
# Offline unit tests (no API key needed)
python -m pytest tests/ -v

# Agent integration tests (require GROQ_API_KEY in .env)
python -m pytest test_compliance.py test_variant.py test_vision_agent.py -v
```

---

## 🔑 Configuration

| Variable | Where | Purpose |
|----------|-------|---------|
| `GROQ_API_KEY` | `.env` | **Required** — all text + vision LLM calls |
| `MAGICHOUR_API_KEY` | `.env` | **Required for post images** — Magic Hour image generation (image node fails gracefully without it) |
| `WANGP_API_URL` | `.env` | Optional — WanGP video endpoint (video node fails gracefully without it) |

Models used (see `config.py` and `graph/nodes.py`):
- **Text agents:** `qwen/qwen3-32b` (Groq)
- **Vision (analysis + scraped-image validation):** Llama-4 vision (Groq) — platform default `PRODUCT_MODEL`
- **Video:** WanGP text/image-to-video (deployed on Modal)
- **Post images:** Magic Hour AI Image Editor (reference image + prompt) / AI Image Generator (text only)

📚 **Full technical details:** see [DOCUMENTATION.md](DOCUMENTATION.md)
