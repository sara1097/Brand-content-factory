# 📚 Technical Documentation — Brand Content Factory (Qwen Edition)

This document explains the internal architecture, every module, the data flow, error handling, and design decisions. For setup and quick start, see [README.md](README.md).

---

## 1. High-level architecture

```
              ┌──────────────────────────────────────────┐
              │               app_qwen.py                │
              │   Streamlit UI — streams the LangGraph   │
              └────────────────────┬─────────────────────┘
                                   ▼
              ┌──────────────────────────────────────────┐
              │      graph/builder.py (StateGraph)       │
              └──────────────────────────────────────────┘

START → acquire_image → product → research → marketing → content
              │                                             │
   (upload OR web-scrape +          ┌───────────┬───────────┤
    vision validation)              ▼           ▼           ▼
                                variants      video       images
                                    │        (WanGP,   (Magic Hour,
                                    │         2 video    4 image
                                    ▼          days)      days)
                                compliance      └────┬──────┘
                                    │                ▼
                                    │            assemble
                                    │       (7-day plan + media)
                                    └───────┬────────┘
                                            ▼
                                          report → END
```

- **Orchestration** is a LangGraph `StateGraph` (`graph/` package). The text-LLM chain is sequential (Groq TPM budget); the two media branches (`video` → Modal, `images` → Magic Hour) run **in parallel** because they talk to separate services and mostly wait on renders.
- **Fault tolerance** is preserved from the old hand-written runner: every node stores `{"node_error": ..., "message": ...}` under its state key instead of raising, so a failing node never kills the run.
- **Downstream nodes degrade gracefully**: if e.g. research failed, marketing receives `{}` for that input instead of crashing (`graph/nodes._ok`).
- **Image acquisition** (`acquire_image`): the uploaded photo is used as-is; without one, `tools/image_scraper.py` downloads DuckDuckGo image candidates and `agents/image_validator_agent.py` keeps the first one the vision model confirms matches the description (confidence ≥ `IMAGE_MATCH_MIN_CONFIDENCE`). If none passes, the run continues without a reference image.
- **The final deliverable** (`assemble` node) is a 7-day plan with an enforced media mix — **2 video days, 4 image days, 1 text-only day** — where each day carries its caption/hashtags/CTA plus the path of its generated video/image.

## 2. Entry point: `app_qwen.py`

| Section | Responsibility |
|---|---|
| Pipeline import | `get_pipeline_graph()` from `graph/builder.py`; model constants and token budgets now live in `graph/nodes.py` |
| Session state | One key per pipeline node + `description`, `image_path`, `pipeline_error`, `current_running_key`; survives Streamlit reruns |
| Graph runner | `graph.stream(..., stream_mode="updates")` — each yielded node result is merged into session state and its card/dashboard re-rendered. UI callbacks (acquisition status, video/image progress bars) travel through `config["configurable"]`; since LangGraph runs nodes in worker threads, callbacks attach Streamlit's script-run context (`add_script_run_ctx`) before touching widgets |
| Rendering engine | Generic recursive JSON→HTML renderer (`render_dict_html`, `render_list_html`, `render_insight_block_html`) — displays any agent output as cards, chips, score badges and collapsible evidence lists without hard-coding each schema |
| Live dashboard | 11 status cards (⚪ Idle / 🟡 Processing / 🟢 Ready / ❌ Error) + progress bar, re-rendered after every node |
| Results sections | Video previews (tagged with their calendar day), Magic Hour image gallery, and the **Final 7-Day Content Plan** (per-day card: caption/hashtags/CTA + attached video/image) |
| Export | Save all node outputs (incl. `image_acquisition`, `images`, `final_calendar`) as timestamped JSON folder, generate PDF via `reports/pdf_generator.py`, download report as TXT |

## 3. Agents (`agents/`)

All text agents inherit from **`base_agent.BaseAgent`**, which centralizes:
- the Groq chat call (via `tools/groq_client.py`),
- system-prompt injection from `agents/prompts/`,
- JSON parsing + schema validation (via `core/validator.py`),
- per-agent settings from `agents/prompts/constants.AGENT_SETTINGS`.

| Agent | Input → Output | Notes |
|---|---|---|
| `image_validator_agent.acquire_product_image` | description (+ optional upload) → validated reference image | Upload wins; otherwise scrapes candidates via `tools/image_scraper.py`, vision-scores **all** of them (`{match, confidence, quality, product_only, background}`) and picks the highest composite score — preferring sharp, watermark-free, product-only shots on a plain white/black background |
| `product_agent.analyze_product` | description + optional image → product intelligence dict | Thin wrapper over `vision_agent` |
| `vision_agent.extract_visual_information` | text + image → structured attributes | Uses `tools/groq_vision.py` (PIL image → base64 → Llama vision), prompt in `prompts/vision_prompt.py` |
| `research_agent.research_market` | product dict → market intelligence | Calls `tools/web_search.collect_market_evidence` (live DuckDuckGo via `ddgs`) for price/competitor sources, then asks the LLM to synthesize **with citations**; caps source counts to control tokens |
| `marketing_strategy_agent.build_marketing_strategy` | product + research + business constraints → strategy | Constraints (country, budget, duration, goal, brand stage) come from the sidebar |
| `content_agent.generate_content` | strategy → 7-day content calendar | Delegates to `content_calendar.generate_content_calendar`; each day carries a `media_type` and `enforce_media_mix()` deterministically guarantees **2 video / 4 image / 1 text** days (config `MEDIA_MIX`) with consistent `content_format`s |
| `variant_agent.generate_variants` | strategy + one calendar day → A/B/C ad variants | Called once **per calendar day** by `graph/nodes.variants_node` with an **anti-repetition memory**: the hooks/CTAs of all previous days (`extract_hooks_and_ctas`) are fed back so no two days reuse an opener, CTA, structure or urgency trigger; banned-phrase lists live in `prompts/variant_prompt.py` (from the `variant_new` branch by Lojain Mohamed) |
| `compliance_agent.generate_compliance` | strategy + one day's variants → compliance review | Called once **per calendar day** by `graph/nodes.compliance_node`, matching the per-day variants — every day's A/B/C set gets its own review; flags risky claims per region |
| `video_agent.generate_video_assets` | description + product + strategy + content (+ image) → 2 rendered videos | The 2 prompts are written from the calendar's **video days** (`prompt_agent`, `days=` param) and each variant is tagged with its day; rendered via `models/wangp_client.py` with progress callbacks |
| `image_agent.generate_image_assets` | description + product + strategy + content (+ image) → 4 rendered images | One Qwen call writes a prompt per **image day**; reference image uploaded to Magic Hour once and reused; falls back to text-only generation if upload fails; deterministic fallback prompts if Qwen's JSON is short |
| `report_agent.generate_report` | all condensed sections → narrative executive report | Feeds the PDF/TXT export |

### Prompt layer (`agents/prompts/`)
- One system prompt per agent (`*_prompt.py`), versioned via `constants.PROMPT_VERSION`.
- `schemas.py` holds the JSON schemas embedded into the prompts so the LLM returns strictly-shaped JSON.
- `constants.AGENT_SETTINGS` holds per-agent defaults (temperature, `num_predict`, …) — overridable per call, which is exactly what `app_qwen.py` does.

## 4. Core services

| Module | Purpose |
|---|---|
| `graph/state.py` | `PipelineState` TypedDict — one key per node output + run inputs |
| `graph/nodes.py` | Fault-tolerant node wrappers around every agent (`_run_node` stores `node_error` instead of raising), model constants + TPM-safe token budgets, `_condense_for_report`, the `assemble_calendar_node` join |
| `graph/builder.py` | `StateGraph` wiring: sequential analysis chain, media fan-out (`content → video/images` in parallel), joins into `assemble` → `report` |
| `tools/groq_client.py` | Single Groq client for the whole app: request building, JSON-mode calls, **retry with backoff on rate limits**, error normalization |
| `tools/groq_vision.py` | Image loading/resizing (PIL), base64 encoding, vision-model call |
| `tools/web_search.py` | DuckDuckGo search wrapper: collects price & competitor evidence, extracts domains/dates for the citation list |
| `tools/image_scraper.py` | DuckDuckGo **image** search: LLM-condensed search query, downloads candidates, PIL-verifies and re-encodes as JPEG (rejects thumbnails < 200px) |
| `tools/magichour_client.py` | Magic Hour API client: pre-signed upload (`/v1/files/upload-urls` + PUT), submit (`/v1/ai-image-editor` with reference, `/v1/ai-image-generator` without), poll `/v1/image-projects/{id}`, download result; returns `{"status": "failed", ...}` instead of raising |
| `tools/profitability.py` | Deterministic profitability math (margins, break-even) — pure Python, fully unit-tested |
| `core/validator.py` | Schema validation of agent outputs + `normalize_reliability` scoring (the 0–1 reliability badges in the UI) |
| `models/llm.py` | `ask_qwen()` convenience helper used by the video/image prompt writers |
| `models/wangp_client.py` | HTTP client for the deployed WanGP video API: submits prompt (+ optional reference image), polls job status, downloads MP4s, reports progress |
| `schemas/` | Pydantic models (`ScenePrompt`, `Storyboard`) that hard-validate the video prompt agent's output |
| `utils/json_parser.py` | Defensive JSON extraction from raw LLM text (handles markdown fences, trailing text) |
| `reports/pdf_*` | ReportLab pipeline: `pdf_styles` (brand styles) → `pdf_components` (paragraph/spacer builders) → `pdf_generator` (document assembly) |

## 5. Data flow & fault tolerance

1. Each node writes its result into `st.session_state[<node>]`.
2. On exception, the node stores `{"node_error": ..., "message": ...}` instead — the dashboard shows ❌ and downstream nodes receive `{}` for that input.
3. Rendering is **schema-agnostic**: whatever JSON an agent returns is rendered recursively, so prompt/schema changes never break the UI.
4. Export only unlocks when the report node succeeded.

## 6. Rate-limit strategy (why the token budgets exist)

Groq enforces ~6000 tokens/min on `qwen/qwen3-32b` for this account tier. Mitigations:
- per-node `num_predict` caps (900–1500 tokens),
- research source caps (5 price + 3 competitor sources),
- report inputs condensed to 300 chars/section,
- retry-with-backoff in `groq_client` for 429 responses,
- vision runs on Llama (separate quota) instead of Qwen-VL, which showed capacity outages.

## 7. Configuration (`config.py` + `.env`)

| Setting | Meaning |
|---|---|
| `GROQ_API_KEY` | Required. Read via `python-dotenv` at import time |
| `MAGICHOUR_API_KEY` | Required for post images (Magic Hour). The `images` node fails gracefully without it |
| `DEFAULT_MODEL` | Default text model for agents (overridden to Qwen by `graph/nodes.py`) |
| `PRODUCT_MODEL` | Vision model (Llama) — also validates scraped images |
| `QWEN_MODEL` | Qwen model id used by the video/image prompt writers |
| `WANGP_API_URL`, `WANGP_NUM_VARIANTS` | Video API endpoint + how many videos to render (2 = the calendar's video days) |
| `MAGICHOUR_API_URL`, `MAGICHOUR_*_SECONDS` | Magic Hour endpoint + poll cadence/timeouts |
| `IMAGE_SCRAPE_MAX_CANDIDATES` | Scraped candidates to try before giving up (default 5) |
| `IMAGE_MATCH_MIN_CONFIDENCE` | Vision confidence needed to accept a scraped image (default 0.6) |
| `MEDIA_MIX` | Weekly plan: `{"video": 2, "image": 4, "text": 1}` |

## 8. Testing

| Test file | Scope | Needs API key? |
|---|---|---|
| `tests/test_validator.py` | schema validation & reliability normalization | ❌ offline |
| `tests/test_profitability.py` | profitability math edge cases (zero price, margin clamping, break-even) | ❌ offline |
| `tests/test_media_mix.py` | `enforce_media_mix` guarantees 2/4/1 on messy LLM output (overshoot, missing types, short/long calendars, format consistency) | ❌ offline |
| `tests/test_assemble_calendar.py` | `assemble_calendar_node` attaches each video/image to its day; missing media marked, errored calendar → `node_error` | ❌ offline |
| `test_compliance.py` | variant → compliance agent chain | ✅ |
| `test_variant.py` | variant generation on a real strategy | ✅ |
| `test_vision_agent.py` | vision extraction | ✅ |
| `test_qwen_vision.py` | raw Qwen-VL API probe (documents the capacity issue) | ✅ |

`conftest.py` adds the project root to `sys.path` so tests run from any directory:

```powershell
.\INSTRUCTOR_ENV\python.exe -m pytest tests/ -v          # offline suite
.\INSTRUCTOR_ENV\python.exe -m pytest -v                 # everything (needs .env)
```

## 9. Bundled environment (`INSTRUCTOR_ENV/`)

A self-contained conda environment (Python **3.11.15**) living inside the project so it can be run with zero setup. It contains exactly the runtime dependencies pinned in `requirements.txt` (streamlit 1.39.0, groq 1.5.0, ddgs 9.14.4, reportlab 5.0.0, pydantic 2.9.2, pillow 10.4.0, python-dotenv 1.0.1, requests 2.32.3) plus `pytest` for the test suite.

Use it either by activating (`conda activate <path>\INSTRUCTOR_ENV`) or directly: `.\INSTRUCTOR_ENV\python.exe -m streamlit run app_qwen.py`.

## 10. Deployment

`Dockerfile` builds a slim Python 3.11 image, installs `requirements.txt`, exposes port 8501 with a Streamlit health check, and starts `app_qwen.py`. Pass secrets with `--env-file .env`.
