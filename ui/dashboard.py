"""Enhanced Dashboard UI Module"""
import streamlit as st
from datetime import datetime
from pathlib import Path


def render_header():
    """Render enhanced header with statistics"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("# 🤖 AI Research Agent Dashboard")
        st.markdown("*Your intelligent market research assistant for Egyptian market*")
    
    with col2:
        st.metric("📊 Analysis Ready", "24/7")
    
    with col3:
        st.metric("🔧 Status", "Active")


def render_quick_stats(total_analyses: int = 0, memory_count: int = 0):
    """Render quick statistics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Analyses", total_analyses, delta="+2")
    
    with col2:
        st.metric("Memory Records", memory_count, delta="+1")
    
    with col3:
        st.metric("Categories", 15, delta="")
    
    with col4:
        st.metric("Last Updated", "now")


def render_quick_actions():
    """Render quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📸 Analyze Image", use_container_width=True):
            st.session_state.current_tab = "image"
            st.rerun()
    
    with col2:
        if st.button("🔍 Compare Products", use_container_width=True):
            st.session_state.current_tab = "compare"
            st.rerun()
    
    with col3:
        if st.button("📊 Market Trends", use_container_width=True):
            st.session_state.current_tab = "trends"
            st.rerun()
    
    with col4:
        if st.button("💡 Get Recommendations", use_container_width=True):
            st.session_state.current_tab = "recommendations"
            st.rerun()


def render_research_history(history_data: list):
    """Render research history with filtering and sorting"""
    st.markdown("### 📚 Recent Research History")
    
    if not history_data:
        st.info("No research history yet. Start by analyzing a product!")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input("🔎 Search history", placeholder="Search by product name...")
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Recent", "Category", "Price Range"])
    
    # Filter and display
    for item in history_data:
        if search_query and search_query.lower() not in str(item).lower():
            continue
        
        with st.expander(f"📦 {item.get('product_name', 'Unknown')} - {item.get('category', 'N/A')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.text(f"Date: {item.get('timestamp', 'N/A')}")
            
            with col2:
                st.text(f"Category: {item.get('category', 'N/A')}")
            
            with col3:
                if st.button("📊 View Full Report", key=f"view_{item.get('id', 'unknown')}"):
                    st.session_state.selected_report = item
                    st.rerun()


def render_insights_panel(insights: dict):
    """Render key insights panel"""
    if not insights:
        return
    
    st.markdown("### 💡 Key Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Market Context")
        market_context = insights.get('market_context', {})
        st.write(f"• Trend: {market_context.get('trend', 'N/A')}")
        st.write(f"• Competition: {market_context.get('competition_level', 'N/A')}")
    
    with col2:
        st.markdown("#### Audience")
        audience = insights.get('audience_persona', {})
        st.write(f"• Segment: {audience.get('segment', 'N/A')}")
        st.write(f"• Budget: {audience.get('budget_range', 'N/A')}")


def render_data_table(data: list, title: str = "Data"):
    """Render data in an interactive table"""
    st.markdown(f"### {title}")
    
    if not data:
        st.info("No data to display")
        return
    
    # Convert to DataFrame for display
    import pandas as pd
    try:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    except:
        st.json(data)


def render_export_section():
    """Render export options"""
    st.markdown("### 📥 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export as PDF", use_container_width=True):
            st.info("PDF export functionality coming soon!")
    
    with col2:
        if st.button("📊 Export as Excel", use_container_width=True):
            st.info("Excel export functionality coming soon!")
    
    with col3:
        if st.button("📋 Copy as JSON", use_container_width=True):
            st.info("JSON copy functionality coming soon!")


def render_settings_sidebar():
    """Render advanced settings in sidebar"""
    with st.sidebar:
        st.markdown("---")
        
        with st.expander("⚙️ Advanced Settings", expanded=False):
            st.markdown("#### Model Settings")
            temperature = st.slider("Temperature", 0.0, 1.0, 0.3, help="Creativity vs consistency")
            max_tokens = st.slider("Max Tokens", 100, 4000, 2000)
            
            st.markdown("#### Research Settings")
            include_web_search = st.checkbox("Include Web Search", value=True)
            use_memory_context = st.checkbox("Use Memory Context", value=True)
            
            st.markdown("#### Display Settings")
            dark_mode = st.checkbox("Dark Mode", value=False)
            compact_view = st.checkbox("Compact View", value=False)
            
            return {
                'temperature': temperature,
                'max_tokens': max_tokens,
                'include_web_search': include_web_search,
                'use_memory_context': use_memory_context,
                'dark_mode': dark_mode,
                'compact_view': compact_view
            }


def render_footer():
    """Render footer with info"""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.caption("Built with Streamlit + CrewAI")
    
    with col2:
        st.caption("Powered by Qwen LLM")
    
    with col3:
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
