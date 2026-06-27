"""Streamlit UI for the local multimodal product research pipeline."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime

import streamlit as st

from agents.product_agent import analyze_product
from agents.research_agent import research_market
from config import MODEL, OUTPUTS_DIR
from memory.vector_store import AgentMemory
from tools.profitability import calculate_profitability, market_price_stats
from tools.reporting import build_html_report


st.set_page_config(page_title="Product Research Agent", page_icon="🔎", layout="wide")


@st.cache_resource
def get_memory() -> AgentMemory:
    return AgentMemory()


memory = get_memory()


def money(value) -> str:
    return "N/A" if value is None else f"{float(value):,.2f} EGP"


def source_table(items: list[dict]) -> list[dict]:
    return [
        {
            "Source": item.get("title"),
            "Price (EGP)": item.get("price_egp"),
            "Confidence": f'{float(item.get("confidence", 0)):.0%}',
            "Domain": item.get("domain"),
            "URL": item.get("url"),
        }
        for item in items
    ]


with st.sidebar:
    st.header("Agent settings")
    st.caption(f"Local model: {MODEL}")
    use_web_search = st.checkbox("Use live web research", value=True)
    use_memory = st.checkbox("Use research memory", value=True)
    save_to_memory = st.checkbox("Save completed research", value=True)
    st.metric("Saved memories", memory.get_all_count())
    if st.button("Clear memory") and memory.clear_all():
        st.success("Memory cleared.")
        st.rerun()


st.title("Product Research Agent")
st.caption("Evidence-backed Egyptian market research, competitor analysis, and unit economics.")

analyze_tab, history_tab, about_tab = st.tabs(["Run analysis", "Saved research", "About"])

with analyze_tab:
    input_col, finance_col = st.columns(2)
    with input_col:
        st.subheader("Product")
        uploaded_image = st.file_uploader("Product image (optional)", type=["jpg", "jpeg", "png", "webp"])
        description = st.text_area(
            "Product description",
            value="Premium wireless earbuds with active noise cancellation and 30-hour battery life",
            height=120,
        )
        if uploaded_image:
            st.image(uploaded_image, width=300)

    with finance_col:
        st.subheader("Unit economics")
        c1, c2 = st.columns(2)
        product_cost = c1.number_input("Product cost (EGP)", min_value=0.0, value=1000.0, step=50.0)
        selling_price = c2.number_input("Planned selling price (EGP)", min_value=0.0, value=1600.0, step=50.0)
        shipping_cost = c1.number_input("Shipping per unit (EGP)", min_value=0.0, value=70.0, step=10.0)
        packaging_cost = c2.number_input("Packaging per unit (EGP)", min_value=0.0, value=30.0, step=5.0)
        platform_fee = c1.number_input("Platform fee (%)", min_value=0.0, max_value=100.0, value=10.0)
        ads_percent = c2.number_input("Advertising cost (%)", min_value=0.0, max_value=100.0, value=8.0)
        other_cost = c1.number_input("Other cost per unit (EGP)", min_value=0.0, value=0.0, step=10.0)
        target_margin = c2.number_input("Target profit margin (%)", min_value=0.0, max_value=95.0, value=25.0)

    run_button = st.button("Run full analysis", type="primary", use_container_width=True)

    if run_button:
        if not description.strip():
            st.error("Enter a product description.")
        else:
            temp_path = None
            try:
                if uploaded_image:
                    suffix = os.path.splitext(uploaded_image.name)[1].lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=OUTPUTS_DIR) as temp_file:
                        temp_file.write(uploaded_image.getvalue())
                        temp_path = temp_file.name

                with st.status("Analyzing product…", expanded=True) as status:
                    product_data = analyze_product(description.strip(), temp_path)
                    if "error" in product_data:
                        raise RuntimeError(f'Product analysis failed: {product_data.get("error")}')
                    st.write(f'Identified: **{product_data.get("product_name", "Unknown")}**')
                    status.update(label="Product identified", state="complete")

                similar_research = []
                if use_memory:
                    with st.status("Checking research memory…") as status:
                        similar_research = memory.search_similar(
                            product_data.get("product_name", ""), product_data.get("category", ""), n_results=2
                        )
                        status.update(label=f"Memory checked ({len(similar_research)} related)", state="complete")

                with st.status("Researching prices and competitors…", expanded=True) as status:
                    market_data = research_market(product_data, use_web_search, similar_research)
                    if "error" in market_data:
                        raise RuntimeError(f'Market research failed: {market_data.get("error")}')
                    sources = market_data.get("data_sources", {})
                    st.write(f'{sources.get("price_source_count", 0)} price sources and '
                             f'{sources.get("competitor_source_count", 0)} competitor sources found.')
                    status.update(label="Market research complete", state="complete")

                profitability = calculate_profitability(
                    product_cost, selling_price, shipping_cost, packaging_cost,
                    platform_fee, ads_percent, other_cost, target_margin,
                )
                report = {
                    "product_analysis": product_data,
                    "market_research": market_data,
                    "profitability": profitability,
                    "market_price_stats": market_price_stats(market_data.get("evidence", {})),
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "model": MODEL,
                        "used_web_search": use_web_search,
                        "used_memory": use_memory,
                    },
                }
                st.session_state["latest_report"] = report

                if save_to_memory:
                    memory.save_research(
                        product_data.get("product_name", "Unknown"),
                        product_data.get("category", "Unknown"),
                        report,
                    )

                filename = f'research_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(OUTPUTS_DIR / filename, "w", encoding="utf-8") as output_file:
                    json.dump(report, output_file, ensure_ascii=False, indent=2)
                st.success("Analysis completed.")
            except Exception as exc:
                st.error(str(exc))
                with st.expander("Technical details"):
                    st.exception(exc)
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    report = st.session_state.get("latest_report")
    if report:
        product = report["product_analysis"]
        market = report["market_research"]
        profit = report["profitability"]
        evidence = market.get("evidence", {})
        stats = report.get("market_price_stats", {})

        st.divider()
        st.subheader("Decision summary")
        decision = market.get("decision", {})
        st.info(market.get("executive_summary", "No summary generated."))
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Verdict", decision.get("verdict", "Needs more evidence"))
        d2.metric("Net profit / unit", money(profit.get("net_profit")))
        d3.metric("Profit margin", f'{profit.get("profit_margin_percent", 0):.2f}%')
        d4.metric("Recommended price", money(profit.get("recommended_price")))
        st.caption(decision.get("rationale", ""))

        st.subheader("Product and market")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Product", product.get("product_name", "Unknown"))
        p2.metric("Category", product.get("category", "Unknown"))
        p3.metric("Median observed price", money(stats.get("median")))
        p4.metric("Observed prices", stats.get("count", 0))

        st.subheader("Price evidence")
        price_rows = source_table(evidence.get("price_sources", []))
        if price_rows:
            st.dataframe(
                price_rows,
                use_container_width=True,
                hide_index=True,
                column_config={"URL": st.column_config.LinkColumn("Source link", display_text="Open")},
            )
        else:
            st.warning("No price evidence was found. Treat pricing recommendations as provisional.")

        st.subheader("Competitor comparison")
        competitors = market.get("competitive_analysis", {}).get("competitors", [])
        if competitors:
            st.dataframe(
                competitors,
                use_container_width=True,
                hide_index=True,
                column_config={"evidence_url": st.column_config.LinkColumn("Evidence", display_text="Open")},
            )
        else:
            st.warning("No competitors were identified from the available evidence.")

        with st.expander("Profitability breakdown", expanded=True):
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("Total unit cost", money(profit.get("total_cost")))
            f2.metric("Break-even price", money(profit.get("break_even_price")))
            f3.metric("ROI", f'{profit.get("roi_percent", 0):.2f}%')
            f4.metric("Target margin", f'{profit.get("target_margin_percent", 0):.2f}%')

        st.subheader("Recommended actions")
        for item in market.get("action_items", []):
            st.markdown(f'**{str(item.get("priority", "")).title()}** — {item.get("action", "")}  \n{item.get("impact", "")}')

        json_data = json.dumps(report, ensure_ascii=False, indent=2)
        html_data = build_html_report(report)
        download_col1, download_col2 = st.columns(2)
        download_col1.download_button(
            "Download complete JSON", json_data, "product_research.json", "application/json", use_container_width=True
        )
        download_col2.download_button(
            "Download printable report", html_data, "product_research.html", "text/html", use_container_width=True
        )
        with st.expander("Full structured output"):
            st.json(report)

with history_tab:
    st.subheader("Saved reports")
    query = st.text_input("Search research memory", placeholder="e.g. wireless earbuds")
    if query:
        for index, item in enumerate(memory.search_similar(query, query, n_results=10), 1):
            with st.expander(f'{index}. {item.get("product_name", "Unknown")} — {item.get("timestamp", "")[:10]}'):
                st.json(item.get("data", {}))
    files = sorted(OUTPUTS_DIR.glob("research_*.json"), reverse=True)[:10]
    for path in files:
        with st.expander(path.name):
            with open(path, encoding="utf-8") as saved_file:
                st.json(json.load(saved_file))
    if not files:
        st.info("No saved reports yet.")

with about_tab:
    st.subheader("How it works")
    st.markdown(
        """
        1. The local multimodal model identifies the product from text and an optional image.
        2. Web research collects traceable price and competitor evidence.
        3. The model produces a grounded market assessment without inventing missing facts.
        4. Unit economics are calculated deterministically from your real costs.
        5. The complete report can be saved, searched, and exported.
        """
    )
