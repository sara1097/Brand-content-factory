# 📊 Brand Content Factory

**Enterprise AI Marketing Intelligence Platform** — an end-to-end AI system that analyzes products, runs market research, builds a marketing strategy, generates content and video, runs compliance checks, and produces an executive PDF report — all through a single Streamlit interface.

---

## 🚀 Main UI

The main entry point of the project is:

```
app_enhanced.py
```

This is the full Streamlit "Enterprise" dashboard that walks through every stage of the pipeline step by step, with the ability to save JSON results and export an executive PDF report.

> Note: the project also includes `app.py` and `app_simple.py` as earlier/simpler variants, but **`app_enhanced.py` is the official, actively used UI**.

### Running the UI

```bash
streamlit run app_enhanced.py
```

---

## 🧩 Pipeline Stages in the UI

The UI walks through the following stages in order, each one unlocking the next:

1. **🛍 Product Input** – enter a product description (text) + an optional product image.
2. **🔍 Analyze Product** – product analysis (Identity / Visual / Feature Intelligence).
3. **🌍 Research Market** – market research grounded in web evidence.
4. **📢 Generate Marketing Strategy** – builds a marketing strategy based on Business Constraints set in the sidebar (country, budget, campaign duration, primary goal, brand stage).
5. **✨ Generate Ad Variants** – generates A/B/C ad variants.
6. **🛡 Compliance Review** – reviews ad variants against advertising policies and rewrites any violations.
7. **📅 Generate Content Calendar** – builds a content plan (static posts, carousels, infographics, polls...).
8. **🎬 Generate Video** – generates video assets (Storyboard + Scene Prompts + final video).
9. **📝 Generate Executive Report** – a comprehensive executive report combining all outputs.
10. **💾 Save Results / 📄 Export PDF** – saves all JSON results to `outputs/<timestamp>/` and exports a downloadable PDF report.

The bottom of the UI also includes:
- **📊 Executive Dashboard**: visual ✅/❌ status indicator for each stage.
- **Pipeline Progress**: a progress bar (X out of 8 stages).
- **🔎 View Complete Pipeline JSON**: view all outputs as a single combined JSON.
- **♻ Reset Session**: fully resets the session state.

---

## 🗂 Project Structure

```
Brand-content-factory-main/
├── app_enhanced.py          # ✅ Main UI (Streamlit) — Enterprise dashboard
├── app.py                   # Alternative version
├── app_simple.py            # Simplified version
├── main.py                  # Runs the pipeline from the terminal (no UI)
├── pipeline.py               # Orchestrates all agents in sequence (Pipeline Orchestrator)
├── config.py                 # Project configuration (Ollama / Groq / Chroma)
├── agents/                   # AI Agents (product, market research, strategy, ad variants, compliance, video, report...)
│   └── prompts/               # System/Task prompts for each agent
├── core/validator.py          # Validates agent outputs
├── memory/vector_store.py     # Vector store (Chroma) for memory/research
├── models/                   # Model clients (LLM, Wan video generator)
├── reports/                  # Executive PDF report generation and formatting
├── schemas/                  # Pydantic schemas (Marketing, Storyboard, Scene Prompt)
├── tools/                    # Helper tools (Groq client, Ollama client, web search, reporting...)
├── ui/dashboard.py            # Additional UI components
├── utils/                    # General utilities (JSON parser, MoviePy builder)
├── data/chroma_db/            # Vector database (Chroma) — generated automatically
├── outputs/                  # Pipeline outputs (JSON + PDF + images)
├── requirements.txt           # Full dependencies
└── requirements-minimal.txt   # Minimal dependencies to run the UI only
```

---

## ⚙️ Tech Stack

- **Streamlit** – the graphical interface.
- **CrewAI / LangChain** – agent orchestration.
- **Groq API** (`llama-3.3-70b-versatile`) – default LLM backend.
- **Ollama** (`qwen3.5:4b` + `nomic-embed-text`) – optional local LLM + embeddings.
- **ChromaDB** – vector storage for market research memory.
- **MoviePy** – assembles video from generated scenes.
- **Internal PDF tooling** (`reports/`) – generates the executive report as a PDF.

---

## 🔑 Configuration & Environment Variables

Create a `.env` file in the project root with:

```env
GROQ_API_KEY=your_groq_api_key_here
```

If you're using Ollama locally, make sure the server is running at:

```
http://localhost:11434
```

(These values are defined in `config.py` and can be edited there directly.)

---

## 📦 Installation & Setup

### 1) Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
```

### 2) Install dependencies

To run the UI only (minimal):

```bash
pip install -r requirements-minimal.txt
```

Or to install everything (including notebook and API tooling):

```bash
pip install -r requirements.txt
```

### 3) Run the main UI

```bash
streamlit run app_enhanced.py
```

This will automatically open the UI in your browser at:
```
http://localhost:8501
```

### Alternative: run without a UI (terminal only)

```bash
python main.py
```

This will prompt you for a product description (and an optional image path), run the full pipeline, and save a PDF report named `Executive_Report.pdf`.

---

## 📤 Outputs

After running the pipeline from the UI, results are saved to:

```
outputs/
├── <timestamp>/
│   ├── product.json
│   ├── research.json
│   ├── marketing.json
│   ├── variants.json
│   ├── compliance.json
│   ├── content.json
│   ├── video.json
│   └── report.json
└── Executive_Report.pdf
```

---

## 📝 Notes

- If an error occurs during any stage, the UI displays it directly (`st.exception`) so you can trace the cause easily.
- The **🗑 Clear Results** button only clears pipeline results, while **♻ Reset Session** fully resets the session state.
- The `data/chroma_db/` folder is generated automatically the first time market research runs — no need to edit it manually.
