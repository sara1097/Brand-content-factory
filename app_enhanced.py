"""
app_enhanced.py

Enterprise AI Marketing Intelligence Platform
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Enterprise AI Marketing Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# IMPORT AGENTS
# ============================================================
from agents.product_agent import analyze_product
from agents.research_agent import research_market
from agents.marketing_strategy_agent import build_marketing_strategy
from agents.report_agent import generate_report
from reports.pdf_generator import generate_pdf
from reports.report_formatter import format_report
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
st.caption("Product Intelligence • Market Intelligence • Marketing Strategy • Executive Report")

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
        st.session_state.report = None
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
        identity = product.get("identity_intelligence", {})
        st.json(identity)
    with tab2:
        visual = product.get("visual_intelligence", {})
        st.json(visual)
    with tab3:
        features = product.get("feature_intelligence", {})
        st.json(features)
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
                research = research_market(st.session_state.product)
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
    product_intelligence=st.session_state.product,
    market_intelligence=st.session_state.research,
    marketing_strategy=st.session_state.marketing,
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
    st.json(st.session_state.report)

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
            formatted_report = format_report(
    st.session_state.report
)
            generate_pdf(formatted_report, str(pdf_path))
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

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Product", "✅" if st.session_state.product else "❌")
with col2:
    st.metric("Market", "✅" if st.session_state.research else "❌")
with col3:
    st.metric("Marketing", "✅" if st.session_state.marketing else "❌")
with col4:
    st.metric("Report", "✅" if st.session_state.report else "❌")

# ============================================================
# PIPELINE STATUS
# ============================================================
completed = sum([
    bool(st.session_state.product),
    bool(st.session_state.research),
    bool(st.session_state.marketing),
    bool(st.session_state.report)
])

progress = completed / 4
st.progress(progress)
st.caption(f"Pipeline Progress: {completed}/4")

# ============================================================
# EXECUTIVE SUMMARY
# ============================================================
if st.session_state.report:
    st.divider()
    st.subheader("📝 Executive Summary")
    summary = st.session_state.report.get("executive_summary", "No summary available.")
    if isinstance(summary, dict):
        st.json(summary)
    else:
        st.write(summary)

# ============================================================
# QUICK INSIGHTS
# ============================================================
if st.session_state.marketing:
    st.divider()
    st.subheader("💡 Quick Insights")
    marketing = st.session_state.marketing
    try:
        exec_strategy = marketing.get("executive_strategy", {})
        st.info(exec_strategy.get("assessment", "No assessment found."))
    except Exception:
        st.info("No executive insights.")

# ============================================================
# RAW JSON
# ============================================================
with st.expander("🔎 View Complete Pipeline JSON"):
    st.json({
        "product": st.session_state.product,
        "research": st.session_state.research,
        "marketing": st.session_state.marketing,
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
st.caption("Enterprise AI Marketing Intelligence Platform")
st.caption("Version 2.0")
st.caption(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")