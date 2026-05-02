import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Trend Backtester", layout="wide")

if "accepted_terms" not in st.session_state:
    st.session_state.accepted_terms = False

if not st.session_state.accepted_terms:
    st.warning("⚠️ You must accept the Terms & Conditions before using this app.")
    if st.button("I Agree to Terms"):
        st.session_state.accepted_terms = True
        st.rerun()
    st.stop()

st.sidebar.title("📊 Navigation")
st.sidebar.markdown("""
- Backtester
- Signal Scanner
- Terms & Conditions
""")

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

if "scan_results" not in st.session_state:
    st.session_state.scan_results = None

if "chart_data" not in st.session_state:
    st.session_state.chart_data = {}

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
st.markdown('<div class="subtitle">Multi-strategy stock backtesting, signal scanning, ranking, and portfolio allocation tool.</div>', unsafe_allow_html=True)

st.divider()

# -----------------------------
# Inputs
# -----------------------------
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    ticker_input = st.text_input(
        "Enter stock symbols",
        "NVDA, MSFT, AAPL, AMZN, GOOGL, META, TSLA, AVGO, LLY, JPM, V, MA, COST, WMT"
    )

with col2:
    start_date = st.date_input("Start Date", pd.to_datetime("2018-01-01"))

with col3:
    initial_capital = st.number_input("Portfolio Capital", value=10000, step=1000)

TICKERS = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

run_button = st.button("🚀 Run Backtest", use_container_width=True)

# -----------------------------
# Data + Strategy Helpers
# -----------------------------
def fix_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


@st.cache_data(show_spinner=False)
def download_data_cached(ticker, start_date_value):
    df = yf.download(
        ticker,
        start=start_date_value,
        interval="1wk",
        auto_adjust=True,
        progress=False
    )

    df = fix_columns(df)

    if df.empty or len(df) < 220:
        return None

    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))
    df["Prev_High"] = df["High"].shift(1)

    return df.dropna()


def download_data(ticker):
    return download_data_cached(ticker, start_date)


def calc_equity_curve(df, buy_col, sell_col):
    capital = 10000
    position = 0
    entry_price = 0
    trades = []
    equity_curve = []

    for date, row in df.iterrows():
        price = float(row["Close"])

        if position == 0 and row[buy_col]:
            position = capital / price
            entry_price = price
            capital = 0

        elif position > 0 and row[sell_col]:
            capital = position * price
            profit = (price - entry_price) / entry_price
            trades.append(profit)
            position = 0

        equity = capital + position * price
        equity_curve.append({"Date": date, "Equity": equity})

    if position > 0:
        final_price = float(df["Close"].iloc[-1])
        profit = (final_price - entry_price) / entry_price
        trades.append(profit)

    return trades, pd.DataFrame(equity_curve)


def calc_stats(ticker, strategy_name, trades, equity_df):
    if len(trades) == 0 or equity_df.empty:
        return None

    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]

    ending_equity = equity_df["Equity"].iloc[-1]
    total_return = (ending_equity - 10000) / 10000 * 100

    peak = equity_df["Equity"].cummax()
    drawdown = (equity_df["Equity"] - peak) / peak
    max_drawdown = drawdown.min() * 100

    win_rate = len(wins) / len(trades) * 100
    avg_win = np.mean(wins) * 100 if wins else 0
    avg_loss = np.mean(losses) * 100 if losses else 0

    if avg_loss != 0:
        ranking_score = (win_rate / 100) * avg_win / abs(avg_loss)
    else:
        ranking_score = 0

    return {
        "Ticker": ticker,
        "Strategy": strategy_name,
        "Trades": len(trades),
        "Win Rate %": round(win_rate, 2),
        "Avg Win %": round(avg_win, 2),
        "Avg Loss %": round(avg_loss, 2),
        "Total Return %": round(total_return, 2),
        "Max Drawdown %": round(max_drawdown, 2),
        "Ranking Score": round(ranking_score, 2),
    }


def trend_strategy(ticker, df):
    df = df.copy()

    df["trend_up"] = df["MA200"] > df["MA200"].shift(20)
    df["strong_trend"] = (df["Close"] > df["MA50"]) & (df["MA50"] > df["MA200"])

    df["buy"] = (
        (df["RSI"] > 45)
        & (df["RSI"] < 70)
        & df["trend_up"]
        & df["strong_trend"]
    )

    df["sell"] = (df["RSI"] < 40) | (df["Close"] < df["MA50"])

    trades, equity_df = calc_equity_curve(df, "buy", "sell")
    stats = calc_stats(ticker, "Trend", trades, equity_df)

    return stats, equity_df


def pullback_strategy(ticker, df):
    df = df.copy()

    trend = df["Close"] > df["MA200"]
    pullback = df["Close"] < df["MA50"]
    breakout = df["Close"] > df["Prev_High"]
    momentum_return = df["RSI"] > 50

    df["buy"] = trend & pullback.shift(1) & breakout & momentum_return
    df["sell"] = (df["Close"] < df["MA50"]) | (df["RSI"] < 45)

    trades, equity_df = calc_equity_curve(df, "buy", "sell")
    stats = calc_stats(ticker, "Pullback", trades, equity_df)

    return stats, equity_df


# -----------------------------
# Backtest
# -----------------------------
if run_button:
    all_results = []
    equity_curves = {}

    progress = st.progress(0)

    for i, ticker in enumerate(TICKERS):
        st.write(f"Running {ticker}...")

        df = download_data(ticker)

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


# -----------------------------
# Signal Scanner
# -----------------------------
st.divider()
st.header("🚨 Signal Scanner")
st.caption("Scan your stock list and show only current BUY / SELL signals.")

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

        df = download_data(ticker)

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
