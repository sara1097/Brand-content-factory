"""
app_qwen.py

Enterprise AI Marketing Intelligence Platform -- Qwen variant.

Same pipeline as app_enhanced.py, but every text agent is pinned to a Qwen
model (qwen/qwen3-32b) instead of the project default (Llama), with
conservative token budgets tuned to fit under this Groq account's measured
6000 TPM ceiling for that model. Vision uses the platform default (Llama)
rather than Qwen's vision model, which has shown repeated server-side
capacity outages on this account. Nothing here changes the default
app_enhanced.py behavior; every override is passed explicitly per call.

UI/UX (single-button, fault-tolerant, collapsible-card pipeline) matches
app_enhanced.py; only the underlying agent calls (models, token budgets,
step order) come from the original app_qwen.py.

Orchestration is a LangGraph StateGraph (graph/builder.py): a sequential
analysis chain, then a parallel fan-out where ad variants, 2 WanGP
videos and 4 Magic Hour images are produced for the 7-day calendar
(2 video days + 4 image days + 1 text-only day), joined into a final
per-day plan with media attached. If no product photo is uploaded, a
web-scraped image validated by the vision model is used instead.
"""

from __future__ import annotations

import html
import json
import threading
from pathlib import Path
from datetime import datetime

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from config import ENABLE_VIDEO_GENERATION, GROQ_API_KEY

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Enterprise AI Marketing Intelligence (Qwen)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# API KEY GUARD
# ============================================================
if not GROQ_API_KEY or GROQ_API_KEY == "your-groq-api-key-here":
    st.error(
        "🔑 **GROQ_API_KEY is missing.** Open the `.env` file in the project "
        "folder and replace the placeholder with your real Groq API key "
        "(free at https://console.groq.com/keys), then refresh this page."
    )
    st.stop()

# ============================================================
# IMPORT PIPELINE (LangGraph) + PDF EXPORT
# ============================================================
# All agent calls, model choices and TPM-safe token budgets now live in
# graph/nodes.py; the execution order lives in graph/builder.py. The app
# only streams the compiled graph and renders each node's output.
from graph.builder import get_pipeline_graph
from graph.nodes import QWEN_TEXT_MODEL, VISION_MODEL
from reports.pdf_generator import generate_pdf

# ============================================================
# OUTPUT DIRECTORY
# ============================================================
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# PIPELINE DEFINITION
# ============================================================
PIPELINE_STEPS = [
    ("image_acquisition", "🔎", "Image Sourcing"),
    ("product", "📦", "Product Intelligence"),
    ("research", "🌍", "Market Intelligence"),
    ("marketing", "📢", "Marketing Strategy"),
    ("content", "📅", "Content Calendar"),
    ("variants", "🎯", "Marketing Variants"),
    ("compliance", "🛡️", "Compliance Review"),
    ("video", "🎬", "AI Videos"),
    ("images", "🖼️", "AI Post Images"),
    ("final_calendar", "🗓️", "Final 7-Day Plan"),
    ("report", "📄", "Executive Report"),
]

# Maps a LangGraph node name to the status line shown when it finishes.
NODE_LABELS = {
    "acquire_image": "🔎 Product image sourcing",
    "product": "📦 Product intelligence",
    "research": "🌍 Market research",
    "marketing": "📢 Marketing strategy",
    "content": "📅 Content calendar",
    "variants": "🎯 Marketing variants",
    "compliance": "🛡️ Compliance review",
    "video": "🎬 AI videos (WanGP)",
    "images": "🖼️ AI post images (Magic Hour)",
    "assemble": "🗓️ Final 7-day plan assembly",
    "report": "📄 Executive report",
}

# ============================================================
# SESSION STATE
# ============================================================
DEFAULT_STATE = {key: None for key, _, _ in PIPELINE_STEPS}
DEFAULT_STATE.update({
    "description": "",
    "image_path": None,
    "pipeline_error": None,
    "current_running_key": None,
})

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# MODERN ENTERPRISE STYLING
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1200px;
    }

    .hero {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border-radius: 16px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero h1 { margin: 0; font-size: 2.2rem; font-weight: 700; color: #ffffff !important; }
    .hero p { margin: 0.5rem 0 0 0; opacity: 0.8; font-size: 1rem; letter-spacing: 0.5px; }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .dash-card {
        padding: 0.85rem 0.5rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        background: #ffffff;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.01);
    }
    .dash-icon { font-size: 1.3rem; margin-bottom: 0.3rem; }
    .dash-label { font-size: 0.78rem; font-weight: 600; color: #64748b; line-height: 1.3; height: 2.2rem; display: flex; align-items: center; justify-content: center; }
    .dash-status { font-size: 0.85rem; margin-top: 0.4rem; font-weight: 600; }

    .kv-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    .kv-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.85rem 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.01);
    }
    .kv-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 0.3rem;
    }
    .kv-value { font-size: 0.95rem; font-weight: 500; color: #1e293b; line-height: 1.5; }
    .kv-empty { color: #cbd5e1; font-style: italic; }

    .nested-block {
        border: 1px solid #f1f5f9;
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 0.95rem;
        font-weight: 700;
        color: #4338ca;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .reliability-row { display: flex; justify-content: flex-end; margin-bottom: 0.75rem; }
    .assessment-box {
        background: #f5f3ff;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #312e81;
    }
    .assessment-line { margin-bottom: 0.4rem; line-height: 1.5; }
    .assessment-line:last-child { margin-bottom: 0; }
    .assessment-label { font-weight: 700; color: #4338ca; }

    details.evidence-box {
        margin-top: 0.75rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
    }
    details.evidence-box summary { cursor: pointer; font-weight: 600; color: #475569; font-size: 0.85rem; outline: none; }
    details.evidence-box ul { margin: 0.5rem 0 0 1.2rem; padding: 0; color: #475569; font-size: 0.85rem; }
    details.evidence-box li { margin-bottom: 0.3rem; line-height: 1.4; }

    .step-nav { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.5rem; }
    .step-nav a {
        text-decoration: none;
        background: #ffffff;
        color: #475569;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 0.4rem 1rem;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .step-nav a:hover { border-color: #6366f1; color: #6366f1; }

    .item-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .item-card-title { font-weight: 700; color: #1e1b4b; margin-bottom: 0.75rem; font-size: 0.95rem; }

    .chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.25rem; margin-bottom: 0.5rem; }
    .chip {
        background: #f1f5f9;
        color: #334155;
        border-radius: 6px;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 500;
        border: 1px solid #e2e8f0;
    }

    .score-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
    .score-high { background: #bbf7d0; color: #15803d; }
    .score-mid  { background: #fef08a; color: #a16207; }
    .score-low  { background: #fecaca; color: #b91c1c; }

    .stExpander {
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
        background: #ffffff !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02) !important;
        overflow: hidden !important;
    }
    
    .plain-value { font-size: 0.95rem; color: #334155; line-height: 1.6; }
    .empty-note { color: #94a3b8; font-style: italic; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# RENDERING HELPERS
# ============================================================
def st_image_full_width(image) -> None:
    """st.image at full column width on any Streamlit version:
    `use_container_width` only exists from 1.40; older versions
    (including the pinned 1.39) take `use_column_width`."""
    try:
        st.image(image, use_container_width=True)
    except TypeError:
        st.image(image, use_column_width=True)


def humanize_key(key: str) -> str:
    return str(key).replace("_", " ").replace("-", " ").strip().title()

def format_simple_value(key: str, value) -> str:
    key_lower = str(key).lower()
    if value is None or value == "": return "<span class='kv-empty'>—</span>"
    if isinstance(value, bool): return "✅ Yes" if value else "❌ No"
    if isinstance(value, (int, float)) and any(t in key_lower for t in ("reliability", "confidence", "score")) and 0 <= float(value) <= 1:
        pct = round(float(value) * 100)
        css_class = "score-high" if pct >= 70 else "score-mid" if pct >= 40 else "score-low"
        return f"<span class='score-badge {css_class}'>{pct}%</span>"
    if key_lower == "status":
        normalized = str(value).strip().lower()
        if normalized in ("success", "ok", "completed", "complete"): return f"<span class='score-badge score-high'>✓ {html.escape(str(value))}</span>"
        if normalized in ("error", "failed", "fail"): return f"<span class='score-badge score-low'>𐄂 {html.escape(str(value))}</span>"
    return html.escape(str(value))

SECTION_ICONS = {"attributes": "🧩", "assessment": "🧭", "evidence": "📎", "data_sources": "🔗", "metadata": "ℹ️", "limitations": "⚠️"}
INSIGHT_KEYS = {"attributes", "assessment", "evidence", "reliability"}

def is_insight_block(data: dict) -> bool:
    keys = set(data.keys())
    return "attributes" in keys and isinstance(data.get("attributes"), dict) and keys.issubset(INSIGHT_KEYS)

def render_insight_block_html(data: dict, depth: int) -> str:
    attributes = data.get("attributes") or {}
    assessment = data.get("assessment") or {}
    evidence = data.get("evidence") or []
    reliability = data.get("reliability")
    parts = []

    if isinstance(reliability, (int, float)) and 0 <= float(reliability) <= 1:
        pct = round(float(reliability) * 100)
        css_class = "score-high" if pct >= 70 else "score-mid" if pct >= 40 else "score-low"
        parts.append(f"<div class='reliability-row'><span class='score-badge {css_class}'>🎯 Reliability: {pct}%</span></div>")

    if attributes: parts.append(render_dict_html(attributes, depth=depth))
    if assessment:
        lines = "".join(f"<div class='assessment-line'><span class='assessment-label'>{html.escape(humanize_key(k))}:</span> {html.escape(str(v)) if str(v).strip() else '—'}</div>" for k, v in assessment.items())
        if lines: parts.append(f"<div class='assessment-box'>{lines}</div>")
    if evidence:
        ev_items = "".join(f"<li>{html.escape(str(e))}</li>" for e in evidence if e not in (None, ""))
        if ev_items: parts.append(f"<details class='evidence-box'><summary>View Verifiable Evidence ({len(evidence)})</summary><ul>{ev_items}</ul></details>")
    return "".join(parts)

def render_dict_html(data: dict, depth: int = 0) -> str:
    if not data: return "<div class='empty-note'>No details available.</div>"
    if is_insight_block(data): return render_insight_block_html(data, depth)
    
    simple_items, complex_items = {}, {}
    for k, v in data.items():
        if isinstance(v, (dict, list)) and v: complex_items[k] = v
        else: simple_items[k] = v if not isinstance(v, (dict, list)) else None
    parts = []

    if simple_items:
        cells = "".join(f"<div class='kv-card'><div class='kv-label'>{html.escape(humanize_key(k))}</div><div class='kv-value'>{format_simple_value(k, v)}</div></div>" for k, v in simple_items.items())
        parts.append(f"<div class='kv-grid'>{cells}</div>")

    for k, v in complex_items.items():
        icon = SECTION_ICONS.get(str(k).lower(), "👉")
        inner = render_value_html(v, depth=depth + 1)
        parts.append(f"<div class='nested-block'><div class='sub-header'>{icon} {html.escape(humanize_key(k))}</div>{inner}</div>")
    return "".join(parts)

def render_list_html(items: list, depth: int = 0) -> str:
    if not items: return "<div class='empty-note'>No records.</div>"
    if all(isinstance(i, dict) for i in items):
        cards = []
        for idx, item in enumerate(items, start=1):
            title = item.get("title") or item.get("name") or item.get("platform") or item.get("day") or item.get("week") or item.get("action") or item.get("id") or f"Entry {idx}"
            cards.append(f"<div class='item-card'><div class='item-card-title'>{idx}. {html.escape(str(title))}</div>{render_dict_html(item, depth=depth + 1)}</div>")
        return "".join(cards)
    if all(isinstance(i, (str, int, float, bool)) or i is None for i in items):
        chips = "".join(f"<span class='chip'>{html.escape(str(i))}</span>" for i in items if i not in (None, ""))
        return f"<div class='chip-row'>{chips}</div>"
    parts = []
    for idx, item in enumerate(items, start=1):
        parts.append(f"<div style='font-weight:600; font-size:0.9rem; margin-top:0.5rem;'>#{idx}</div>")
        parts.append(render_value_html(item, depth=depth + 1))
    return "".join(parts)

def render_value_html(value, depth: int = 0) -> str:
    if value is None: return "<div class='empty-note'>—</div>"
    if isinstance(value, dict): return render_dict_html(value, depth=depth)
    if isinstance(value, list): return render_list_html(value, depth=depth)
    if isinstance(value, bool): return f"<div class='plain-value'>{'✅ Yes' if value else '❌ No'}</div>"
    if isinstance(value, str):
        text = html.escape(value).replace("\n", "<br>") if value.strip() else "—"
        return f"<div class='plain-value'>{text}</div>"
    return f"<div class='plain-value'>{html.escape(str(value))}</div>"

def render_section(icon: str, title: str, step_num: int, data) -> None:
    is_expanded = (step_num == 1)
    if title == "Executive Report" and isinstance(data, dict):
        keys_to_delete = {
            "implementation_roadmap", "implementation roadmap",
            "kpi_framework", "kpi framework",
            "executive_verdict", "executive verdict",
            "narrative_report", "narrative report"
        }
        data = {k: v for k, v in data.items() if str(k).lower().strip() not in keys_to_delete}

    with st.expander(f"{step_num}️⃣ {icon} {title}", expanded=is_expanded):
        body_html = render_value_html(data, depth=0)
        st.markdown(f"<div class='step-body'>{body_html}</div>", unsafe_allow_html=True)

# ============================================================
# HEADER & STATIC APP HERO
# ============================================================
st.markdown(
    f"""<div class="hero"><h1>📊 Enterprise AI Marketing Intelligence Platform</h1>
    <p>Qwen text agents ({QWEN_TEXT_MODEL}) + Llama vision ({VISION_MODEL})</p></div>""",
    unsafe_allow_html=True,
)

# ============================================================
# LIVE EXECUTIVE DASHBOARD PLACEHOLDER
# ============================================================
st.markdown("<div class='section-title'>📈 Real-time Pipeline Status</div>", unsafe_allow_html=True)
dashboard_placeholder = st.empty()

def render_live_dashboard():
    with dashboard_placeholder.container():
        dash_cols = st.columns(len(PIPELINE_STEPS))
        for col, (key, icon, title) in zip(dash_cols, PIPELINE_STEPS):
            state_val = st.session_state.get(key)
            
            if state_val is not None and isinstance(state_val, dict) and "node_error" in state_val:
                status_icon = "<span style='color: #b91c1c;'>❌ Error</span>"
            elif state_val is not None:
                status_icon = "<span style='color: #15803d;'>🟢 Ready</span>"
            elif st.session_state.current_running_key == key:
                status_icon = "<span style='color: #b45309;'>🟡 Processing...</span>"
            else:
                status_icon = "<span style='color: #94a3b8;'>⚪ Idle</span>"

            card_html = f"""
            <div class='dash-card'>
                <div class='dash-icon'>{icon}</div>
                <div class='dash-label'>{html.escape(title)}</div>
                <div class='dash-status'>{status_icon}</div>
            </div>
            """
            with col:
                st.markdown(card_html, unsafe_allow_html=True)
        
        resolved_nodes = sum(st.session_state.get(key) is not None for key, _, _ in PIPELINE_STEPS)
        progress = resolved_nodes / len(PIPELINE_STEPS)
        st.progress(progress)
        st.caption(f"Engine Processing Integrity: {resolved_nodes} out of {len(PIPELINE_STEPS)} nodes diagnostic verified")

# Render Initial Static State
render_live_dashboard()

# ============================================================
# SIDEBAR CONFIGURATION
# ============================================================
with st.sidebar:
    st.header("⚙️ Business Constraints")
    country = st.selectbox("Country", ["Egypt", "Saudi Arabia", "UAE", "Qatar", "Kuwait"])
    budget = st.selectbox("Budget", ["Low", "Medium", "High"])
    campaign_duration = st.selectbox("Campaign Duration", ["1 Month", "3 Months", "6 Months", "12 Months"])
    primary_goal = st.selectbox("Primary Goal", ["Increase Sales", "Brand Awareness", "Lead Generation", "Market Expansion"])
    brand_stage = st.selectbox("Brand Stage", ["New Product Launch", "Growth", "Mature", "Rebranding"])

    st.header("🧪 Generation Options")
    enable_video = st.checkbox(
        "🎬 Generate AI videos (WanGP)",
        value=ENABLE_VIDEO_GENERATION,
        help="Videos take ~10 minutes on the Modal GPU. Turn off for fast "
             "test runs — the rest of the pipeline (images, calendar, report) "
             "still runs normally.",
    )

business_constraints = {"country": country, "budget": budget, "campaign_duration": campaign_duration, "primary_goal": primary_goal, "brand_stage": brand_stage}

# ============================================================
# PRODUCT DATA CONFIGURATION INPUTS
# ============================================================
st.markdown("<div class='section-title'>🛍️ Product Input</div>", unsafe_allow_html=True)
with st.container(border=True):
    description = st.text_area("Product Description", height=150, placeholder="Describe your product...")
    uploaded_image = st.file_uploader("Optional Product Image", type=["png", "jpg", "jpeg"])
    image_path = None
    if uploaded_image:
        image_path = OUTPUT_DIR / uploaded_image.name
        with open(image_path, "wb") as f:
            f.write(uploaded_image.read())
        image_path = str(image_path)
        st.image(uploaded_image, caption=f"Loaded Asset: {uploaded_image.name}", width=240)

# ============================================================
# RESULTS CONTAINERS PLACEHOLDERS (For real-time step outputs)
# ============================================================
st.markdown("<div class='section-title'>🗂️ Analysis Results Node</div>", unsafe_allow_html=True)

cards_placeholders = {key: st.empty() for key, _, _ in PIPELINE_STEPS}
video_player_placeholder = st.empty()

def render_step_card_live(step_key: str):
    for idx, (key, icon, title) in enumerate(PIPELINE_STEPS, start=1):
        if key == step_key and st.session_state.get(key):
            with cards_placeholders[key].container():
                render_section(icon, title, idx, st.session_state[key])

# ريندير الكروت المخزنة مسبقاً أول ما الصفحة تفتح أو يعاد بناؤها
for key, _, _ in PIPELINE_STEPS:
    render_step_card_live(key)

# ============================================================
# MULTI-AGENT EXECUTION RUNNER (Fault-Tolerant Loop Mode)
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
run_col, clear_col = st.columns([4, 1])

with run_col:
    run_clicked = st.button("🚀 Run Full Pipeline", use_container_width=True, type="primary")
with clear_col:
    clear_clicked = st.button("🗑️ Reset Workspace", use_container_width=True)

if clear_clicked:
    for key, _, _ in PIPELINE_STEPS:
        st.session_state[key] = None
    st.session_state.pipeline_error = None
    st.session_state.current_running_key = None
    st.rerun()

if run_clicked:
    if not description.strip():
        st.warning("Please enter a product description.")
    else:
        st.session_state.description = description
        st.session_state.image_path = image_path
        for key, _, _ in PIPELINE_STEPS:
            st.session_state[key] = None
        st.session_state.pipeline_error = None
        st.session_state.current_running_key = None
        
        for kp in cards_placeholders.values():
            kp.empty()
        video_player_placeholder.empty()
        render_live_dashboard()

        status_box = st.status("Running the LangGraph pipeline (fault-tolerant mode)...", expanded=True)

        with status_box:
            # UI callbacks are invoked from LangGraph worker threads;
            # Streamlit widgets only work there once the script-run
            # context is attached to that thread.
            script_ctx = get_script_run_ctx()

            def _attach_ctx():
                try:
                    add_script_run_ctx(threading.current_thread(), script_ctx)
                except Exception:
                    pass

            acquire_status_holder = st.empty()
            video_bar_holder = st.empty()
            image_bar_holder = st.empty()

            def _on_acquire_status(text):
                _attach_ctx()
                acquire_status_holder.caption(f"🔎 {text}")

            def _on_video_progress(variant, total, pct, status, phase):
                _attach_ctx()
                total = total or 1
                fraction = (pct or 0) / 100
                overall = min(max(((variant - 1) + fraction) / total, 0.0), 1.0)
                label = f"🎬 Video {variant}/{total}: {status}"
                if pct is not None: label += f" ({pct}%)"
                if phase: label += f" — {phase}"
                video_bar_holder.progress(overall, text=label)

            def _on_image_progress(index, total, text):
                _attach_ctx()
                image_bar_holder.progress(min(max(index / max(total, 1), 0.0), 1.0), text=f"🖼️ {text}")

            def _first_pending_key():
                for key, _, _ in PIPELINE_STEPS:
                    if st.session_state.get(key) is None:
                        return key
                return None

            initial_state = {
                "description": description,
                "uploaded_image_path": image_path,
                "business_constraints": business_constraints,
                "enable_video": enable_video,
            }
            run_config = {"configurable": {
                "on_acquire_status": _on_acquire_status,
                "on_video_progress": _on_video_progress,
                "on_image_progress": _on_image_progress,
            }}

            st.session_state.current_running_key = "image_acquisition"
            render_live_dashboard()

            try:
                for update in get_pipeline_graph().stream(initial_state, config=run_config, stream_mode="updates"):
                    for node_name, delta in update.items():
                        if not isinstance(delta, dict):
                            continue

                        for key, value in delta.items():
                            st.session_state[key] = value
                            render_step_card_live(key)

                        label = NODE_LABELS.get(node_name, node_name)
                        node_errors = [
                            v["node_error"] for v in delta.values()
                            if isinstance(v, dict) and "node_error" in v
                        ]
                        if node_errors:
                            st.error(f"Node Error [{label}]: {node_errors[0]}")
                        else:
                            st.write(f"{label} — done ✓")

                        # Show the scraped product image as soon as the
                        # vision model has validated one.
                        if node_name == "acquire_image":
                            acquisition = st.session_state.get("image_acquisition") or {}
                            if acquisition.get("source") == "scraped":
                                st.image(
                                    acquisition["image_path"],
                                    caption="Web-scraped product image (validated by the vision model)",
                                    width=240,
                                )
                            acquire_status_holder.empty()

                        st.session_state.current_running_key = _first_pending_key()
                        render_live_dashboard()
            except Exception as e:
                st.session_state.pipeline_error = str(e)
                st.error(f"Pipeline error: {e}")

            video_bar_holder.empty()
            image_bar_holder.empty()
            st.session_state.current_running_key = None
            render_live_dashboard()

        status_box.update(label="✅ Pipeline run completed (review node errors below if any)", state="complete", expanded=False)

# ============================================================
# PERSISTENT MULTI-MODAL PLAYER
# ============================================================
if st.session_state.get("video") and "node_error" not in st.session_state["video"]:
    with video_player_placeholder.container():
        video_data = st.session_state["video"]
        if video_data.get("variants"):
            st.markdown("<div style='font-size:0.95rem; font-weight:700; color:#312e81; margin: 0.5rem 0;'>🎬 Rendered AI Video Previews</div>", unsafe_allow_html=True)
            v_variants = video_data["variants"]
            v_cols = st.columns(len(v_variants) or 1)
            for col, variant in zip(v_cols, v_variants):
                with col:
                    day_label = f" — Day {variant['day']}" if variant.get("day") else ""
                    st.markdown(f"**Variant {variant.get('variant')}{day_label}**")
                    st.caption(variant.get("prompt", ""))
                    if variant.get("status") == "succeeded" and variant.get("video_path"):
                        st.video(variant["video_path"])
                    else:
                        st.error(variant.get("error", "Generation failed"))

# ============================================================
# GENERATED POST IMAGES GALLERY (Magic Hour)
# ============================================================
if st.session_state.get("images") and "node_error" not in st.session_state["images"]:
    images_data = st.session_state["images"]
    if images_data.get("images"):
        st.markdown("<div style='font-size:0.95rem; font-weight:700; color:#312e81; margin: 0.5rem 0;'>🖼️ Generated Post Images</div>", unsafe_allow_html=True)
        img_items = images_data["images"]
        img_cols = st.columns(len(img_items) or 1)
        for col, item in zip(img_cols, img_items):
            with col:
                st.markdown(f"**Day {item.get('day')}**")
                if item.get("status") == "succeeded" and item.get("image_path"):
                    st_image_full_width(item["image_path"])
                    st.caption(item.get("prompt", "")[:140])
                else:
                    st.error(item.get("error", "Generation failed"))

# ============================================================
# FINAL 7-DAY CONTENT PLAN (text + attached media per day)
# ============================================================
if st.session_state.get("final_calendar") and "node_error" not in st.session_state["final_calendar"]:
    final_plan = st.session_state["final_calendar"]
    st.markdown("<div class='section-title'>🗓️ Final 7-Day Content Plan</div>", unsafe_allow_html=True)
    mix = final_plan.get("media_mix", {})
    st.caption(
        f"Campaign: {final_plan.get('campaign_name', '—')} · "
        f"{mix.get('video', 0)} video days · {mix.get('image', 0)} image days · "
        f"{mix.get('text', 0)} text-only day"
    )
    MEDIA_BADGES = {"video": "🎬 Video", "image": "🖼️ Image", "text": "✍️ Text only"}
    for day in final_plan.get("days", []):
        media_type = day.get("media_type", "text")
        with st.container(border=True):
            text_col, media_col = st.columns([3, 2])
            with text_col:
                st.markdown(
                    f"**Day {day.get('day')} — {MEDIA_BADGES.get(media_type, media_type)}** · "
                    f"{day.get('platform', '')} · {day.get('content_format', '')}"
                )
                if day.get("hook"):
                    st.markdown(f"*{day['hook']}*")
                if day.get("caption"):
                    st.write(day["caption"])
                if day.get("hashtags"):
                    st.caption(" ".join(day["hashtags"]))
                if day.get("cta"):
                    st.caption(f"CTA: {day['cta']}")
            with media_col:
                if media_type == "text":
                    st.caption("No media required for this day.")
                elif day.get("media_status") == "skipped":
                    st.caption("Video generation was disabled for this run.")
                elif day.get("media_status") == "succeeded" and day.get("media_path"):
                    if media_type == "video":
                        st.video(day["media_path"])
                    else:
                        st_image_full_width(day["media_path"])
                else:
                    st.warning(day.get("media_error") or f"Media {day.get('media_status', 'missing')}.")

            extra = day.get("extra_caption")
            if extra:
                source_note = (
                    "Compliance-reviewed ad variant"
                    if extra.get("source") == "compliance_safe"
                    else "Ad variant (compliance review unavailable)"
                )
                with st.expander("➕ Extra caption / more options"):
                    if extra.get("hook"):
                        st.markdown(f"*{extra['hook']}*")
                    if extra.get("body"):
                        st.write(extra["body"])
                    if extra.get("cta"):
                        st.caption(f"CTA: {extra['cta']}")
                    st.caption(source_note)

# ============================================================
# STRATEGIC ASSET DATA EXPORT
# ============================================================
if st.session_state.get("report") and "node_error" not in st.session_state.report:
    st.markdown("<div class='section-title'>💾 Export</div>", unsafe_allow_html=True)
    save_col, pdf_col = st.columns(2)

    with save_col:
        if st.button("💾 Save Results (JSON)", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_folder = OUTPUT_DIR / timestamp
            output_folder.mkdir(exist_ok=True)
            files = {
                "image_acquisition.json": st.session_state.image_acquisition,
                "product.json": st.session_state.product, "research.json": st.session_state.research,
                "marketing.json": st.session_state.marketing, "content.json": st.session_state.content,
                "variants.json": st.session_state.variants, "compliance.json": st.session_state.compliance,
                "video.json": st.session_state.video, "images.json": st.session_state.images,
                "final_calendar.json": st.session_state.final_calendar,
                "report.json": st.session_state.report,
            }
            for filename, data in files.items():
                with open(output_folder / filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            st.success(f"Saved to {output_folder}")

    with pdf_col:
        if st.button("📄 Export PDF", use_container_width=True):
            pdf_path = OUTPUT_DIR / "Executive_Report.pdf"
            try:
                generate_pdf(st.session_state.report.get("narrative_report", ""), str(pdf_path))
                st.success("PDF generated successfully.")
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="⬇ Download PDF", data=pdf_file, file_name="Executive_Report.pdf",
                        mime="application/pdf", use_container_width=True,
                    )
            except Exception as exc:
                st.exception(exc)

    if st.session_state.report.get("narrative_report"):
        st.download_button(
            label="⬇ Download Report (Text)", data=st.session_state.report.get("narrative_report", ""),
            file_name="Executive_Report.txt", mime="text/plain", use_container_width=True,
        )

# ============================================================
# FOOTER
# ============================================================
st.divider()
foot_col1, foot_col2 = st.columns(2)
with foot_col1:
    st.caption("Enterprise AI Marketing Intelligence Platform -- Qwen variant")
with foot_col2:
    st.caption(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")