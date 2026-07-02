# AI Marketing Intelligence Platform

## Introduction

The AI Marketing Intelligence Platform turns one product description, plus
an optional photo, into a complete go-to-market package. It runs eight AI
agents in sequence. Each agent handles one task: product identification,
market research, marketing strategy, content planning, ad copy, compliance
review, video planning, and executive reporting.

The platform targets a specific gap. Small businesses and solo founders need
market research, a marketing strategy, compliant ad copy, and a content plan
before launching a product. Building these normally takes a specialist and
several days. Most AI marketing tools skip straight to ad copy from a vague
prompt, with no grounding in real market data. This platform grounds its
research in real, traceable web evidence and keeps every source visible to
the user.

## Architecture

The pipeline is linear. Each agent consumes the previous agent's output and
produces structured data for the next one.

```
Product Photo/Description
        │
        ▼
 1. Vision / Product Agent   — identifies the product from image + text
        │
        ▼
 2. Research Agent           — market research grounded in real web evidence
        │
        ▼
 3. Marketing Strategy Agent — STP, SWOT, pricing, channels, budget, KPIs
        │
        ▼
 4. Content Calendar Agent   — 7-day social content plan
        │
        ▼
 5. Variant Agent            — 3 ad copy variants (emotional/rational/urgency)
        │
        ▼
 6. Compliance Agent         — rewrites any variant that violates ad policy
        │
        ▼
 7. Video Agent              — storyboard and scene prompts
        │
        ▼
 8. Report Agent             — executive report as JSON and plain text
```

Every agent returns a structured result. On failure, it returns an error
object instead of raising an exception. One failed web search or malformed
model response degrades a single stage. It does not crash the run.

## Tools and technologies

| Category | Tool | Role |
|---|---|---|
| LLM inference | [Groq](https://groq.com) | Runs Llama, Qwen, and OpenAI open-weight models with low latency |
| Web interface | [Streamlit](https://streamlit.io) | The interactive UI for running the pipeline and viewing results |
| Vector memory | [ChromaDB](https://www.trychroma.com) | Stores and searches past research results |
| Web search | [ddgs](https://pypi.org/project/ddgs/) | Collects real DuckDuckGo search results as market evidence |
| PDF generation | [ReportLab](https://www.reportlab.com) | Renders the executive report as a downloadable PDF |
| Data validation | [Pydantic](https://docs.pydantic.dev) | Validates structured data passed between the video pipeline's stages |
| Image processing | [Pillow](https://pillow.readthedocs.io) | Resizes and re-encodes uploaded product photos before analysis |
| Testing | [pytest](https://pytest.org) | Runs the automated test suite |
| Containerization | [Docker](https://www.docker.com) | Packages the platform for deployment |

## Key features

- **Evidence-grounded research.** The research agent works from real
  DuckDuckGo search results, not invented facts. Every price and competitor
  claim links back to a source URL. Each source carries a confidence score
  based on domain trust — established Egyptian retailers like Amazon.eg,
  Noon, and Jumia rank higher than unknown domains. When evidence is
  missing, the agent reports "insufficient evidence" instead of guessing.
- **Deterministic financial calculations.** Profitability, margin, ROI, and
  break-even price are computed with plain arithmetic. No model estimates a
  number that a calculator can compute exactly.
- **Dual-format reporting.** The executive report is generated once and
  presented two ways: structured JSON for downstream use, and a
  plain-English narrative built from that same JSON. No second model call
  is needed to produce the readable version.
- **PDF export.** The plain-English report renders directly to a PDF with
  real headings and bullet lists.
- **Two model configurations.** Text agents run on either Llama or Qwen,
  selectable by which app file you launch; vision always runs on Llama.
  See [Model configurations](#model-configurations) below.
- **Automatic retry logic.** Rate limit and transient server errors trigger
  an automatic retry with exponential backoff, honoring the provider's own
  retry-after guidance.
- **Containerized deployment.** A Dockerfile builds a self-contained image;
  configuration lives in a single `.env` file.

## Agent reference

| Agent | Input | Output | Example output field |
|---|---|---|---|
| **Vision / Product** | Text description, optional photo | Product identity and attributes | `"product_name": "Wireless Earbuds"` |
| **Research** | Product output | Market context, competitors, pricing decision, evidence | `"decision": {"verdict": "Proceed", "recommended_price_range": "800-1200 EGP"}` |
| **Marketing Strategy** | Product + Research outputs, business constraints | STP, SWOT, pricing, channel, campaign, budget strategy | `"swot_analysis": {"strengths": [...], "weaknesses": [...]}` |
| **Content Calendar** | Marketing output | 7-day content plan | `"days": [{"platform": "Instagram", "hook": "..."}]` |
| **Variants** | Marketing + Content Calendar outputs | 3 ad copy variants | `"variant_a": {"angle": "Emotional", "hook": "..."}` |
| **Compliance** | Marketing + Variants outputs | Policy-safe rewrite of each variant | `"compliance_flags": ["Removed unverified claim"]` |
| **Video** | Product + Marketing + Content outputs | Storyboard and scene prompts | `"storyboard": {"scenes": [...]}` |
| **Report** | Product + Research + Marketing (required); Variants, Compliance, Content (optional) | Executive report, JSON and plain text | `"narrative_report": "EXECUTIVE BUSINESS REPORT\n..."` |

Business constraints passed into the Marketing Strategy agent include
country, budget level, campaign duration, primary goal, and brand stage.
These shape the recommendations without needing a separate agent.

## Model configurations

The platform ships two Streamlit apps. Both run the identical pipeline
above; they differ only in which LLM provider settings their text agents
use.

| | `app_enhanced.py` | `app_qwen.py` |
|---|---|---|
| Vision model | `meta-llama/llama-4-scout-17b-16e-instruct` | Same |
| Text model | `llama-3.3-70b-versatile` | `qwen/qwen3-32b` |
| Token budget per request (text) | Standard | Reduced, for accounts with a lower per-model rate limit |

Both apps use the same Llama vision model. Use `app_enhanced.py` by
default. Use `app_qwen.py` on a Groq account where Qwen's text model
carries a tighter rate limit than Llama's — its request sizes are tuned to
fit within that limit. Full configuration details are in
[`APP_QWEN.md`](APP_QWEN.md).

## Project structure

```
agents/                 One module per pipeline stage
  prompts/               System and task prompt text, shared constants
tools/                   Groq client, vision client, web search, profitability math
reports/                 PDF generation
schemas/                 Pydantic schemas for the video pipeline
core/validator.py        Shared output-shape validation
memory/vector_store.py   ChromaDB-backed research memory
tests/                   pytest suite
config.py                Central configuration: models, paths, API key
pipeline.py              CLI pipeline runner
main.py                  CLI entry point
app_enhanced.py          Primary Streamlit app (Llama)
app_qwen.py              Alternate Streamlit app (Qwen)
app.py                   Standalone research tool with a profitability calculator
```

## Getting started

Install dependencies and configure the API key:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # then set GROQ_API_KEY
```

Run the main app:

```bash
streamlit run app_enhanced.py
```

Run the Qwen configuration instead:

```bash
streamlit run app_qwen.py
```

Run the pipeline from the command line:

```bash
python main.py
```

Run with Docker:

```bash
docker build -t ai-marketing-platform .
docker run -p 8501:8501 --env-file .env ai-marketing-platform
```

## Testing

```bash
pytest tests/
```

The suite covers deterministic logic that does not call an LLM: output
validation (`core/validator.py`) and profitability calculations
(`tools/profitability.py`).

## Roadmap

- Real video rendering. The video agent currently produces a storyboard and
  scene prompts only.
- Automated tests against a mocked Groq client, covering the agent layer.
- An orchestration framework (e.g. LangGraph), if the pipeline grows
  branches, parallel stages, or needs mid-run checkpointing. The current
  linear flow does not require one.
