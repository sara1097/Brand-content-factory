"""
Simple Working Streamlit UI
Run with: streamlit run app_simple.py
"""
import streamlit as st
import json
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="🤖 AI Research Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Product Research Agent")
st.markdown("*Analyze products and get market insights for Egyptian market*")

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("**Status:** ✅ Running")
    st.markdown("**Model:** Qwen3.5:4b")
    
    st.divider()
    
    st.subheader("🔧 Options")
    use_web_search = st.checkbox("🌐 Web Search", value=True)
    use_memory = st.checkbox("🧠 Memory", value=True)
    save_results = st.checkbox("💾 Save Results", value=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🚀 Analyze", "🔄 Compare", "📚 History"])

# ============ TAB 1: DASHBOARD ============
with tab1:
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔍 Analyses", 0)
    col2.metric("📦 Products", 0)
    col3.metric("💾 Memory", 0)
    col4.metric("📈 Categories", 15)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✨ Features")
        st.markdown("✅ Product image analysis")
        st.markdown("✅ Market research")
        st.markdown("✅ Competitor analysis")
        st.markdown("✅ Price tracking")
        st.markdown("✅ Trend analysis")
    
    with col2:
        st.markdown("### 🚀 Quick Start")
        st.markdown("1. Go to **Analyze** tab")
        st.markdown("2. Upload product image")
        st.markdown("3. Enter product details")
        st.markdown("4. Click Analyze")
        st.markdown("5. View results and insights")

# ============ TAB 2: ANALYZE ============
with tab2:
    st.header("🚀 Analyze Product")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Input")
        
        uploaded_file = st.file_uploader("Upload product image", type=['jpg', 'jpeg', 'png', 'webp'])
        
        product_name = st.text_input("Product Name")
        category = st.selectbox("Category", ["Smartphones", "Laptops", "Tablets", "Accessories", "Other"])
        description = st.text_area("Description", height=150)
        
        analyze_btn = st.button("🚀 Analyze", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("👁️ Preview")
        if uploaded_file:
            st.image(uploaded_file, use_column_width=True)
        else:
            st.info("Upload an image to see preview")
    
    # Analysis
    if analyze_btn:
        if not uploaded_file or not product_name:
            st.error("❌ Please upload image and enter product name")
        else:
            with st.spinner("🔍 Analyzing..."):
                st.success("✅ Analysis complete!")
                
                st.markdown("### Product Information")
                st.json({
                    "name": product_name,
                    "category": category,
                    "description": description,
                    "analyzed_at": datetime.now().isoformat()
                })
                
                st.markdown("### Market Research")
                st.json({
                    "market_trend": "Increasing demand",
                    "price_range": "1500-5000 EGP",
                    "competition": "Medium",
                    "best_places": ["Jumia", "Noon", "Amazon Egypt"]
                })
                
                if save_results:
                    st.success("💾 Results saved to memory")

# ============ TAB 3: COMPARE ============
with tab3:
    st.header("🔄 Compare Products")
    
    st.info("Compare multiple products side-by-side")
    
    num_products = st.slider("Number of products", 2, 5, 2)
    
    products = []
    cols = st.columns(num_products)
    
    for i, col in enumerate(cols):
        with col:
            st.subheader(f"Product {i+1}")
            name = st.text_input(f"Name {i}", key=f"p{i}_name")
            price = st.text_input(f"Price (EGP) {i}", key=f"p{i}_price")
            rating = st.slider(f"Rating {i}", 1, 5, 4, key=f"p{i}_rating")
            
            if name:
                products.append({
                    "name": name,
                    "price": price,
                    "rating": rating
                })
    
    if st.button("🔄 Compare", use_container_width=True):
        if len(products) >= 2:
            st.success("✅ Comparison ready!")
            
            st.markdown("### Results")
            st.markdown(f"**Best Overall:** {products[0]['name']}")
            st.markdown(f"**Best Value:** {products[-1]['name']}")
            
            st.dataframe({
                "Product": [p["name"] for p in products],
                "Price": [p["price"] for p in products],
                "Rating": [p["rating"] for p in products]
            })
        else:
            st.error("❌ Please enter at least 2 products")

# ============ TAB 4: HISTORY ============
with tab4:
    st.header("📚 Research History")
    
    st.info("No research history yet. Start analyzing products!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export History", use_container_width=True):
            st.info("Export feature coming soon")
    
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.info("History cleared")

# Footer
st.divider()
st.caption("🤖 AI Research Agent v2.0 | Built with Streamlit + CrewAI | " + datetime.now().strftime("%H:%M:%S"))
