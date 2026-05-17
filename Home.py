import streamlit as st

st.set_page_config(page_title="Trend Strategy Backtester", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
.main { background-color: #f8fafc; }
.big-title {
    font-size: 48px;
    font-weight: 800;
}
.subtitle {
    color: #64748b;
    font-size: 20px;
    margin-bottom: 20px;
}
.feature-card {
    background-color: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    height: 100%;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">📈 Trend Strategy Backtester</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Test Trend and Pullback strategies across your selected stock list.</div>', unsafe_allow_html=True)

st.info("Welcome! This is a Streamlit prototype designed for multi-strategy stock backtesting and daily signal scanning. Use the links below or the sidebar to navigate the tool.")

st.subheader("🚀 Quick Links")
col_link1, col_link2, col_link3 = st.columns(3)
with col_link1:
    st.page_link("pages/1_Backtester.py", label="Multi-Strategy Backtester", icon="📊")
with col_link2:
    st.page_link("pages/2_Signal_Scanner.py", label="Active Signal Scanner", icon="🚨")
with col_link3:
    st.page_link("pages/3_Terms_and_Conditions.py", label="Terms & Conditions", icon="📄")

st.divider()

st.subheader("✨ Key Features")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Multi-Strategy Backtesting</h3>
        <p>Test and compare robust Trend and Pullback strategies across customizable watchlists to find the best performing approaches.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🚨 Active Signal Scanner</h3>
        <p>Scan your favorite stocks to find real-time, actionable BUY and SELL signals based on historical backtest logic.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>💼 Portfolio Allocation & Equity Curve</h3>
        <p>Analyze suggested capital allocation and visualize historical performance with interactive equity curves.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.subheader("📸 Previews")

c1, c2, c3 = st.columns(3)

with c1:
    st.image("screenshots/back-test-results.png", caption="Detailed Backtest Results & Equity Curves", use_column_width=True)
with c2:
    st.image("screenshots/top-5-stocks-to-buy.png", caption="Top 5 Opportunities Ranked by Score", use_column_width=True)
with c3:
    st.image("screenshots/active-signals.png", caption="Active Signal Scanner", use_column_width=True)
