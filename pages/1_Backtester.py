import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import download_data_cached, trend_strategy, pullback_strategy

st.set_page_config(page_title="Trend Backtester", layout="wide")

if "accepted_terms" not in st.session_state:
    st.session_state.accepted_terms = False

if not st.session_state.accepted_terms:
    st.warning("⚠️ You must accept the Terms & Conditions before using this app.")
    if st.button("I Agree to Terms"):
        st.session_state.accepted_terms = True
        st.rerun()
    st.stop()

# -----------------------------
# Session State
# -----------------------------
if "backtest_results" not in st.session_state:
    st.session_state.backtest_results = None
if "best_per_stock" not in st.session_state:
    st.session_state.best_per_stock = None
if "top5" not in st.session_state:
    st.session_state.top5 = None
if "equity_curves" not in st.session_state:
    st.session_state.equity_curves = {}
if "tickers" not in st.session_state:
    st.session_state.tickers = "NVDA, MSFT, AAPL, AMZN, GOOGL, META, TSLA, AVGO, LLY, JPM, V, MA, COST, WMT"
if "start_date" not in st.session_state:
    st.session_state.start_date = pd.to_datetime("2018-01-01")

# -----------------------------
# UI Style
# -----------------------------
st.markdown("""
<style>
.main { background-color: #f8fafc; }
.big-title {
    font-size: 42px;
    font-weight: 800;
}
.subtitle {
    color: #64748b;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">📊 Trend Strategy Backtester</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-strategy stock backtesting, ranking, and portfolio allocation tool.</div>', unsafe_allow_html=True)

st.divider()

# -----------------------------
# Inputs
# -----------------------------
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    ticker_input = st.text_input("Enter stock symbols", st.session_state.tickers)
    st.session_state.tickers = ticker_input

with col2:
    start_date_input = st.date_input("Start Date", st.session_state.start_date)
    st.session_state.start_date = pd.to_datetime(start_date_input)

with col3:
    initial_capital = st.number_input("Portfolio Capital", value=10000, step=1000)

TICKERS = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

run_button = st.button("🚀 Run Backtest", use_container_width=True)

# -----------------------------
# Backtest
# -----------------------------
if run_button:
    all_results = []
    equity_curves = {}

    progress = st.progress(0)

    for i, ticker in enumerate(TICKERS):
        st.write(f"Running {ticker}...")

        df = download_data_cached(ticker, st.session_state.start_date)

        if df is None:
            progress.progress((i + 1) / len(TICKERS))
            continue

        trend_stats, trend_equity = trend_strategy(ticker, df)
        pullback_stats, pullback_equity = pullback_strategy(ticker, df)

        if trend_stats:
            all_results.append(trend_stats)
            equity_curves[(ticker, "Trend")] = trend_equity

        if pullback_stats:
            all_results.append(pullback_stats)
            equity_curves[(ticker, "Pullback")] = pullback_equity

        progress.progress((i + 1) / len(TICKERS))

    results_df = pd.DataFrame(all_results)

    if results_df.empty:
        st.warning("No valid results found.")
    else:
        best_per_stock = (
            results_df.sort_values("Ranking Score", ascending=False)
            .groupby("Ticker")
            .head(1)
            .sort_values("Ranking Score", ascending=False)
        )

        top5 = best_per_stock.head(5).copy()

        top5["Allocation %"] = top5["Ranking Score"] / top5["Ranking Score"].sum() * 100
        top5["Allocation $"] = top5["Allocation %"] / 100 * initial_capital

        st.session_state.backtest_results = results_df
        st.session_state.best_per_stock = best_per_stock
        st.session_state.top5 = top5
        st.session_state.equity_curves = equity_curves


# -----------------------------
# Display Backtest Results
# -----------------------------
if st.session_state.top5 is not None:
    results_df = st.session_state.backtest_results
    top5 = st.session_state.top5
    equity_curves = st.session_state.equity_curves

    st.divider()

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Stocks Tested", len(TICKERS))
    m2.metric("Best Stock", top5.iloc[0]["Ticker"])
    m3.metric("Best Strategy", top5.iloc[0]["Strategy"])
    m4.metric("Top Score", top5.iloc[0]["Ranking Score"])

    st.subheader("🔥 Top 5 Stocks to Buy Now")

    st.dataframe(
        top5[
            [
                "Ticker",
                "Strategy",
                "Ranking Score",
                "Win Rate %",
                "Total Return %",
                "Max Drawdown %",
                "Allocation %",
                "Allocation $",
            ]
        ],
        use_container_width=True,
    )

    st.subheader("💼 Portfolio Allocation")

    fig_alloc = px.pie(
        top5,
        names="Ticker",
        values="Allocation %",
        title="Suggested Allocation by Ranking Score",
    )
    st.plotly_chart(fig_alloc, use_container_width=True)

    st.subheader("📈 Equity Curve")

    selected_ticker = st.selectbox(
        "Select stock",
        top5["Ticker"].tolist(),
        key="equity_selectbox"
    )

    selected_strategy = top5[top5["Ticker"] == selected_ticker]["Strategy"].iloc[0]
    selected_equity = equity_curves.get((selected_ticker, selected_strategy))

    if selected_equity is not None:
        fig = px.line(
            selected_equity,
            x="Date",
            y="Equity",
            title=f"{selected_ticker} - {selected_strategy} Strategy Equity Curve",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 All Strategy Results")

    st.dataframe(
        results_df.sort_values("Ranking Score", ascending=False),
        use_container_width=True,
    )
