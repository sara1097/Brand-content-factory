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
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import streamlit as st

from config import PRODUCT_MODEL

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
# IMPORT AGENTS
# ============================================================
from agents.variant_agent import generate_variants
from agents.product_agent import analyze_product
from agents.research_agent import research_market
from agents.marketing_strategy_agent import build_marketing_strategy
from agents.report_agent import generate_report
from reports.pdf_generator import generate_pdf
from agents.compliance_agent import generate_compliance
from agents.content_agent import generate_content
from agents.video_agent import generate_video_assets

# ============================================================
# MODELS + TPM-SAFE TOKEN BUDGETS
# ============================================================
# Text agents use Qwen; this account's measured limit for qwen/qwen3-32b is
# 6000 tokens/minute. A single request's cost is roughly
# system_prompt + input_data + max_completion tokens, so every text budget
# below leaves real headroom under that ceiling even with a full pipeline's
# worth of input data.
#
# Vision uses the platform default (Llama) instead of Qwen: the Qwen vision
# model (qwen/qwen3.6-27b) has shown repeated server-side capacity outages
# on this account, independent of token budget or image size.

VISION_MODEL = PRODUCT_MODEL
QWEN_TEXT_MODEL = "qwen/qwen3-32b"

VISION_MAX_TOKENS = 700          # vision JSON schema is ~14 short fields
RESEARCH_SETTINGS = {"num_predict": 1500}
RESEARCH_MAX_PRICE_SOURCES = 5
RESEARCH_MAX_COMPETITOR_SOURCES = 3
MARKETING_SETTINGS = {"num_predict": 900}
CONTENT_MAX_TOKENS = 2000
VARIANT_SETTINGS = {"num_predict": 1200}
COMPLIANCE_SETTINGS = {"num_predict": 1200}
REPORT_SETTINGS = {"num_predict": 1200}
REPORT_SECTION_MAX_CHARS = 300   # bounds each report input section's size


def _condense_for_report(data: dict | None, max_chars: int = REPORT_SECTION_MAX_CHARS) -> dict:
    """
    Bound every top-level field's size before it reaches the report
    prompt, so the report step's total size stays predictable regardless
    of how verbose upstream agents get -- the report system prompt alone
    is already ~2100 tokens, leaving little room to spare under 6000 TPM.
    """
    if not data:
        return {}
    condensed = {}
    for key, value in data.items():
        if key in {"data_sources", "metadata", "evidence", "strategy_score"}:
            continue
        text = json.dumps(value, ensure_ascii=False)
        condensed[key] = value if len(text) <= max_chars else text[:max_chars] + "...(truncated)"
    return condensed


# ============================================================
# OUTPUT DIRECTORY
# ============================================================
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# SESSION STATE
# ============================================================
DEFAULT_STATE = {
    "product": None,
    "research": None,
    "marketing": None,
    "content": None,
    "variants": None,
    "compliance": None,
    "video": None,
    "report": None,
    "image_path": None,
    "description": "",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# HEADER
# ============================================================
st.title("📊 Enterprise AI Marketing Intelligence Platform")
st.caption(f"Qwen text agents ({QWEN_TEXT_MODEL}) + Llama vision ({VISION_MODEL})")
st.info(
    "Text agents use Qwen with reduced token budgets to stay under this "
    "account's tight rate limit. Vision uses Llama instead of Qwen, since "
    "the Qwen vision model has shown repeated capacity outages on this "
    "account. Text outputs may be more concise than the default (Llama) "
    "app as a result of the reduced budgets."
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ Business Constraints")

    country = st.selectbox(
        "Country",
        ["Egypt", "Saudi Arabia", "UAE", "Qatar", "Kuwait"]
    )

    budget = st.selectbox(
        "Budget",
        ["Low", "Medium", "High"]
    )

    campaign_duration = st.selectbox(
        "Campaign Duration",
        ["1 Month", "3 Months", "6 Months", "12 Months"]
    )

    primary_goal = st.selectbox(
        "Primary Goal",
        ["Increase Sales", "Brand Awareness", "Lead Generation", "Market Expansion"]
    )

    brand_stage = st.selectbox(
        "Brand Stage",
        ["New Product Launch", "Growth", "Mature", "Rebranding"]
    )

business_constraints = {
    "country": country,
    "budget": budget,
    "campaign_duration": campaign_duration,
    "primary_goal": primary_goal,
    "brand_stage": brand_stage,
}

# ============================================================
# PRODUCT INPUT
# ============================================================
st.subheader("🛍 Product Input")

description = st.text_area(
    "Product Description",
    height=180,
    placeholder="Describe your product..."
)

uploaded_image = st.file_uploader(
    "Optional Product Image",
    type=["png", "jpg", "jpeg"]
)

image_path = None
if uploaded_image:
    image_path = OUTPUT_DIR / uploaded_image.name
    with open(image_path, "wb") as f:
        f.write(uploaded_image.read())
    image_path = str(image_path)

# ============================================================
# PRODUCT ANALYSIS
# ============================================================
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🔍 Analyze Product", use_container_width=True):
        if not description.strip():
            st.warning("Please enter a product description.")
        else:
            with st.spinner("Analyzing Product..."):
                try:
                    product = analyze_product(
                        text_description=description,
                        image_path=image_path,
                        model=VISION_MODEL,
                        max_completion_tokens=VISION_MAX_TOKENS,
                    )
                    if "error" in product:
                        st.error(product["error"])
                    else:
                        st.session_state.product = product
                        st.session_state.description = description
                        st.success("Product analysis completed.")
                except Exception as exc:
                    st.exception(exc)

with col2:
    if st.button("🗑 Clear Results", use_container_width=True):
        st.session_state.product = None
        st.session_state.research = None
        st.session_state.marketing = None
        st.session_state.variants = None
        st.session_state.report = None
        st.session_state.compliance = None
        st.session_state.content = None
        st.session_state.video = None
        st.rerun()

# ============================================================
# DISPLAY PRODUCT RESULT
# ============================================================
if st.session_state.product:
    st.divider()
    st.subheader("📦 Product Intelligence")
    product = st.session_state.product

    tab1, tab2, tab3, tab4 = st.tabs(["Identity", "Visual", "Features", "JSON"])

    with tab1:
        st.json({
            "product_name": product.get("product_name"),
            "brand": product.get("brand"),
            "category": product.get("category"),
            "subcategory": product.get("subcategory"),
            "product_type": product.get("product_type"),
        })

    with tab2:
        st.json({
            "colors": product.get("colors"),
            "materials": product.get("materials"),
            "design_style": product.get("design_style"),
            "shape": product.get("shape"),
            "surface_finish": product.get("surface_finish"),
        })

    with tab3:
        st.json({
            "features": product.get("features"),
            "visible_text": product.get("visible_text"),
            "visible_logos": product.get("visible_logos"),
        })

    with tab4:
        st.json(product)

# ============================================================
# MARKET RESEARCH
# ============================================================
st.divider()
st.subheader("🌍 Market Intelligence")

if st.button("📈 Research Market", use_container_width=True):
    if not st.session_state.product:
        st.warning("Analyze a product first.")
    else:
        with st.spinner("Researching Market..."):
            try:
                research = research_market(
                    st.session_state.product,
                    model=QWEN_TEXT_MODEL,
                    settings_overrides=RESEARCH_SETTINGS,
                    max_price_sources=RESEARCH_MAX_PRICE_SOURCES,
                    max_competitor_sources=RESEARCH_MAX_COMPETITOR_SOURCES,
                )
                if "error" in research:
                    st.error(research["error"])
                else:
                    st.session_state.research = research
                    st.success("Market research completed.")
            except Exception as exc:
                st.exception(exc)

if st.session_state.research:
    st.subheader("📊 Market Intelligence Result")
    st.json(st.session_state.research)

# ============================================================
# MARKETING STRATEGY
# ============================================================
st.divider()
st.subheader("📢 Marketing Strategy")

if st.button("🚀 Generate Marketing Strategy", use_container_width=True):
    if st.session_state.product is None:
        st.warning("Analyze the product first.")
    elif st.session_state.research is None:
        st.warning("Run Market Research first.")
    else:
        with st.spinner("Generating Marketing Strategy..."):
            try:
                marketing = build_marketing_strategy(
                    product_intelligence=st.session_state.product,
                    market_intelligence=st.session_state.research,
                    business_constraints=business_constraints,
                    model=QWEN_TEXT_MODEL,
                    settings_overrides=MARKETING_SETTINGS,
                )
                if "error" in marketing:
                    st.error(marketing["error"])
                else:
                    st.session_state.marketing = marketing
                    st.success("Marketing Strategy generated successfully.")
            except Exception as exc:
                st.exception(exc)

if st.session_state.marketing:
    st.subheader("📈 Marketing Strategy Result")
    st.json(st.session_state.marketing)

# ============================================================
# CONTENT CALENDAR
# ============================================================
st.divider()
st.subheader("📅 Content Calendar")

if st.button("📅 Generate Content Calendar", use_container_width=True):
    if st.session_state.marketing is None:
        st.warning("Generate Marketing Strategy first.")
    else:
        with st.spinner("Generating Content Calendar..."):
            try:
                content = generate_content(
                    st.session_state.marketing,
                    model=QWEN_TEXT_MODEL,
                    max_completion_tokens=CONTENT_MAX_TOKENS,
                )
                st.session_state.content = content
                st.success("Content Calendar generated.")
            except Exception as exc:
                st.exception(exc)

if st.session_state.content:
    st.subheader("📅 Generated Content")
    st.json(st.session_state.content)

# ============================================================
# VARIANT GENERATION
# ============================================================
st.divider()
st.subheader("🎯 Marketing Variants")

if st.button("✨ Generate Ad Variants", use_container_width=True):
    if st.session_state.marketing is None:
        st.warning("Generate Marketing Strategy first.")
    else:
        with st.spinner("Generating Marketing Variants..."):
            try:
                variants = generate_variants(
                    st.session_state.marketing,
                    st.session_state.content,
                    model=QWEN_TEXT_MODEL,
                    settings_overrides=VARIANT_SETTINGS,
                )
                if "error" in variants:
                    st.error(variants["error"])
                else:
                    st.session_state.variants = variants
                    st.success("Marketing Variants generated successfully.")
            except Exception as exc:
                st.exception(exc)

if st.session_state.variants:
    st.subheader("🎨 Generated Variants")
    st.json(st.session_state.variants)

# ============================================================
# COMPLIANCE REVIEW
# ============================================================
st.divider()
st.subheader("🛡 Compliance Review")

if st.button("🛡 Generate Compliance", use_container_width=True):
    if st.session_state.marketing is None:
        st.warning("Generate Marketing Strategy first.")
    elif st.session_state.variants is None:
        st.warning("Generate Variants first.")
    else:
        with st.spinner("Checking Compliance..."):
            try:
                compliance = generate_compliance(
                    st.session_state.marketing,
                    st.session_state.variants,
                    model=QWEN_TEXT_MODEL,
                    settings_overrides=COMPLIANCE_SETTINGS,
                )
                st.session_state.compliance = compliance
                st.success("Compliance completed.")
            except Exception as exc:
                st.exception(exc)

if st.session_state.compliance:
    st.subheader("🛡 Compliance Result")
    st.json(st.session_state.compliance)

# ============================================================
# VIDEO GENERATION
# ============================================================
st.divider()
st.subheader("🎬 AI Video")
st.caption(
    f"Two DISTINCT creative prompts (enhanced by Qwen: {QWEN_TEXT_MODEL}, "
    "grounded in your marketing strategy + content plan), each rendered as "
    "its own separate video via the deployed WanGP API."
)

if st.button("🎥 Generate Video", use_container_width=True):
    if not description.strip():
        st.warning("Please enter a product description first.")
    else:
        total_variants = 2  # WANGP_NUM_VARIANTS
        progress_bar = st.progress(0, text="Enhancing prompts with Qwen...")
        variant_status = st.empty()

        def _on_video_progress(variant, total, pct, status, phase):
            # Overall progress = variants fully done + current variant's
            # fractional progress, spread evenly across all variants.
            total = total or total_variants
            done_variants = variant - 1
            fraction = (pct or 0) / 100
            overall = (done_variants + fraction) / total
            overall = min(max(overall, 0.0), 1.0)
            label = f"Variant {variant}/{total}: {status}"
            if pct is not None:
                label += f" ({pct}%)"
            if phase:
                label += f" — {phase}"
            progress_bar.progress(overall, text=label)
            variant_status.caption(label)

        try:
            video = generate_video_assets(
                description=description,
                product=st.session_state.product,
                marketing=st.session_state.marketing,
                content=st.session_state.content,
                image_path=image_path,
                on_progress=_on_video_progress,
            )
            if "error" in video:
                progress_bar.empty()
                variant_status.empty()
                st.error(video["error"])
            else:
                st.session_state.video = video
                progress_bar.progress(1.0, text="Done — 2 videos rendered")
                variant_status.empty()
                st.success("Videos generated.")
        except Exception as exc:
            progress_bar.empty()
            variant_status.empty()
            st.exception(exc)

if st.session_state.video:
    st.subheader("🎬 Generated Video")

    if "variants" in st.session_state.video:
        variants = st.session_state.video["variants"]
        cols = st.columns(len(variants) or 1)
        for col, variant in zip(cols, variants):
            with col:
                st.markdown(f"**Variant {variant.get('variant')}**")
                st.caption(variant.get("prompt", ""))
                if variant.get("status") == "succeeded" and variant.get("video_path"):
                    st.video(variant["video_path"])
                else:
                    st.error(variant.get("error", "Generation failed"))

        with st.expander("Raw video result JSON"):
            st.json(st.session_state.video)
    else:
        st.json(st.session_state.video)



# ============================================================
# EXECUTIVE REPORT
# ============================================================
st.divider()
st.subheader("📄 Executive Report")

if st.button("📝 Generate Executive Report", use_container_width=True):
    if st.session_state.marketing is None:
        st.warning("Generate Marketing Strategy first.")
    else:
        with st.spinner("Generating Executive Report..."):
            try:
                report = generate_report(
                    product_intelligence=_condense_for_report(st.session_state.product),
                    market_intelligence=_condense_for_report(st.session_state.research),
                    marketing_strategy=_condense_for_report(st.session_state.marketing),
                    variants=_condense_for_report(st.session_state.variants),
                    compliance=_condense_for_report(st.session_state.compliance),
                    content=_condense_for_report(st.session_state.content),
                    model=QWEN_TEXT_MODEL,
                    settings_overrides=REPORT_SETTINGS,
                )
                if "error" in report:
                    st.error(report["error"])
                else:
                    st.session_state.report = report
                    st.success("Executive Report generated.")
            except Exception as exc:
                st.exception(exc)

if st.session_state.report:
    st.subheader("📋 Executive Report")
    report_text_tab, report_json_tab = st.tabs(["Readable Report", "JSON"])
    with report_text_tab:
        st.text(st.session_state.report.get("narrative_report", "No narrative report available."))
    with report_json_tab:
        st.json(st.session_state.report)

    st.download_button(
        label="⬇ Download Report (Text)",
        data=st.session_state.report.get("narrative_report", ""),
        file_name="Executive_Report.txt",
        mime="text/plain",
        use_container_width=True,
    )

# ============================================================
# SAVE JSON FILES
# ============================================================
if st.session_state.report:
    if st.button("💾 Save Results", use_container_width=True):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = OUTPUT_DIR / timestamp
        output_folder.mkdir(exist_ok=True)

        files = {
            "product.json": st.session_state.product,
            "research.json": st.session_state.research,
            "marketing.json": st.session_state.marketing,
            "content.json": st.session_state.content,
            "variants.json": st.session_state.variants,
            "compliance.json": st.session_state.compliance,
            "video.json": st.session_state.video,
            "report.json": st.session_state.report,
        }

        for filename, data in files.items():
            with open(output_folder / filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        st.success(f"Saved to {output_folder}")

# ============================================================
# PDF EXPORT
# ============================================================
if st.session_state.report:
    if st.button("📄 Export PDF", use_container_width=True):
        pdf_path = OUTPUT_DIR / "Executive_Report.pdf"
        try:
            generate_pdf(st.session_state.report.get("narrative_report", ""), str(pdf_path))
            st.success("PDF generated successfully.")

            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="⬇ Download PDF",
                    data=pdf_file,
                    file_name="Executive_Report.pdf",
                    mime="application/pdf",
                )
        except Exception as exc:
            st.exception(exc)

# ============================================================
# DASHBOARD
# ============================================================
st.divider()
st.header("📊 Executive Dashboard")

col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
with col1:
    st.metric("Product", "✅" if st.session_state.product else "❌")
with col2:
    st.metric("Market", "✅" if st.session_state.research else "❌")
with col3:
    st.metric("Marketing", "✅" if st.session_state.marketing else "❌")
with col4:
    st.metric("Content", "✅" if st.session_state.content else "❌")
with col5:
    st.metric("Variants", "✅" if st.session_state.variants else "❌")
with col6:
    st.metric("Compliance", "✅" if st.session_state.compliance else "❌")
with col7:
    st.metric("Video", "✅" if st.session_state.video else "❌")
with col8:
    st.metric("Report", "✅" if st.session_state.report else "❌")

# ============================================================
# PIPELINE STATUS
# ============================================================
completed = sum([
    bool(st.session_state.product),
    bool(st.session_state.research),
    bool(st.session_state.marketing),
    bool(st.session_state.content),
    bool(st.session_state.variants),
    bool(st.session_state.compliance),
    bool(st.session_state.video),
    bool(st.session_state.report),
])

progress = completed / 8

st.progress(progress)
st.caption(f"Pipeline Progress: {completed}/8")

# ============================================================
# RAW JSON
# ============================================================
with st.expander("🔎 View Complete Pipeline JSON"):
    st.json({
        "product": st.session_state.product,
        "research": st.session_state.research,
        "marketing": st.session_state.marketing,
        "content": st.session_state.content,
        "variants": st.session_state.variants,
        "compliance": st.session_state.compliance,
        "video": st.session_state.video,
        "report": st.session_state.report,
    })

# ============================================================
# RESET
# ============================================================
st.divider()
if st.button("♻ Reset Session", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Enterprise AI Marketing Intelligence Platform -- Qwen variant")
st.caption(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")