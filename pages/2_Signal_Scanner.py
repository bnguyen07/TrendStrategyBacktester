import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import download_data_cached, trend_strategy, pullback_strategy

st.set_page_config(page_title="Signal Scanner", layout="wide")

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
if "scan_results" not in st.session_state:
    st.session_state.scan_results = None
if "chart_data" not in st.session_state:
    st.session_state.chart_data = {}
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

st.markdown('<div class="big-title">🚨 Signal Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Scan your stock list and show only current BUY / SELL signals.</div>', unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    ticker_input = st.text_input("Enter stock symbols", st.session_state.tickers)
    st.session_state.tickers = ticker_input

with col2:
    start_date_input = st.date_input("Start Date", st.session_state.start_date)
    st.session_state.start_date = pd.to_datetime(start_date_input)

TICKERS = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

scan_button = st.button("🔍 Run Signal Scanner", use_container_width=True)

def get_current_signal(ticker, df, strategy):
    latest = df.iloc[-1]

    if strategy == "Trend":
        trend_up = latest["MA200"] > df["MA200"].shift(20).iloc[-1]
        strong_trend = latest["Close"] > latest["MA50"] and latest["MA50"] > latest["MA200"]

        buy = (
            latest["RSI"] > 45
            and latest["RSI"] < 70
            and trend_up
            and strong_trend
        )

        sell = latest["RSI"] < 40 or latest["Close"] < latest["MA50"]

        reason_buy = "Strong uptrend + RSI in buy zone"
        reason_sell = "RSI weak or price below MA50"

    else:
        trend = latest["Close"] > latest["MA200"]
        pullback_yesterday = df["Close"].iloc[-2] < df["MA50"].iloc[-2]
        breakout = latest["Close"] > df["High"].iloc[-2]
        momentum_return = latest["RSI"] > 50

        buy = trend and pullback_yesterday and breakout and momentum_return
        sell = latest["Close"] < latest["MA50"] or latest["RSI"] < 45

        reason_buy = "Pullback completed + breakout + RSI above 50"
        reason_sell = "Price below MA50 or RSI below 45"

    if buy:
        return "BUY", reason_buy

    if sell:
        return "SELL", reason_sell

    return "HOLD", "No active signal"


def add_signal_chart(ticker, df):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["MA50"],
        mode="lines",
        name="MA50"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["MA200"],
        mode="lines",
        name="MA200"
    ))

    fig.update_layout(
        title=f"{ticker} Price Chart",
        height=600,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)


if scan_button:
    signal_rows = []
    chart_data = {}
    scanner_progress = st.progress(0)

    for i, ticker in enumerate(TICKERS):
        st.write(f"Scanning {ticker}...")

        df = download_data_cached(ticker, st.session_state.start_date)

        if df is None:
            scanner_progress.progress((i + 1) / len(TICKERS))
            continue

        trend_stats, _ = trend_strategy(ticker, df)
        pullback_stats, _ = pullback_strategy(ticker, df)

        possible = []

        if trend_stats:
            possible.append(trend_stats)

        if pullback_stats:
            possible.append(pullback_stats)

        if not possible:
            scanner_progress.progress((i + 1) / len(TICKERS))
            continue

        best_strategy = sorted(
            possible,
            key=lambda x: x["Ranking Score"],
            reverse=True
        )[0]["Strategy"]

        signal, reason = get_current_signal(ticker, df, best_strategy)

        if signal in ["BUY", "SELL"]:
            latest = df.iloc[-1]

            signal_rows.append({
                "Ticker": ticker,
                "Strategy": best_strategy,
                "Signal": signal,
                "Price": round(float(latest["Close"]), 2),
                "RSI": round(float(latest["RSI"]), 2),
                "Reason": reason,
            })

            chart_data[ticker] = df

        scanner_progress.progress((i + 1) / len(TICKERS))

    st.session_state.scan_results = pd.DataFrame(signal_rows)
    st.session_state.chart_data = chart_data


# -----------------------------
# Display Scanner Results
# -----------------------------
if st.session_state.scan_results is not None:
    signal_df = st.session_state.scan_results

    if signal_df.empty:
        st.success("No active BUY / SELL signals right now.")
    else:
        st.subheader("📌 Active Signals")

        st.dataframe(signal_df, use_container_width=True)

        selected_signal = st.selectbox(
            "Select ticker to view chart",
            signal_df["Ticker"].tolist(),
            key="signal_chart_selectbox"
        )

        selected_df = st.session_state.chart_data.get(selected_signal)

        if selected_df is not None:
            add_signal_chart(selected_signal, selected_df)
