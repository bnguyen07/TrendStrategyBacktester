import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.title("📊 Multi-Strategy Backtester")

TICKERS = [
    "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "LLY", "JPM",
    "V", "MA", "UNH", "XOM", "COST", "WMT", "HD", "PG", "JNJ", "ORCL",
    "ABBV", "NFLX", "BAC", "KO", "AMD", "CRM", "PEP", "ADBE", "TMO", "CSCO",
    "LIN", "MCD", "ACN", "ABT", "WFC", "GE", "QCOM", "TXN", "INTU", "PM",
    "AMAT", "ISRG", "NOW", "IBM", "CAT", "GS", "MS", "UBER", "RTX", "SPGI"
]

start_date = st.date_input("Start Date", pd.to_datetime("2018-01-01"))
run_button = st.button("Run Backtest")


def fix_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def calc_stats(ticker, strategy_name, trades):
    if len(trades) == 0:
        return None

    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]

    win_rate = len(wins) / len(trades) * 100
    avg_win = np.mean(wins) * 100 if wins else 0
    avg_loss = np.mean(losses) * 100 if losses else 0

    # Simple ranking score
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
        "Ranking Score": round(ranking_score, 2),
    }


def download_data(ticker):
    df = yf.download(
        ticker,
        start=start_date,
        interval="1wk",
        auto_adjust=True,
        progress=False
    )

    df = fix_columns(df)

    if df.empty or len(df) < 200:
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


def trend_strategy(ticker, df):
    trades = []
    position = 0
    entry_price = 0

    df["trend_up"] = df["MA200"] > df["MA200"].shift(20)
    df["strong_trend"] = (df["Close"] > df["MA50"]) & (df["MA50"] > df["MA200"])

    df["buy"] = (
        (df["RSI"] > 45)
        & (df["RSI"] < 70)
        & df["trend_up"]
        & df["strong_trend"]
    )

    df["sell"] = (df["RSI"] < 40) | (df["Close"] < df["MA50"])

    for _, row in df.iterrows():
        price = row["Close"]

        if position == 0 and row["buy"]:
            position = 1
            entry_price = price

        elif position == 1 and row["sell"]:
            profit = (price - entry_price) / entry_price
            trades.append(profit)
            position = 0

    return calc_stats(ticker, "Trend", trades)


def pullback_strategy(ticker, df):
    trades = []
    position = 0
    entry_price = 0

    # TSLA-style logic:
    # Big trend must still be up
    trend = df["Close"] > df["MA200"]

    # Pullback happened recently
    pullback = df["Close"] < df["MA50"]

    # Re-entry confirmation
    breakout = df["Close"] > df["Prev_High"]
    momentum_return = df["RSI"] > 50

    df["buy"] = trend & pullback.shift(1) & breakout & momentum_return

    # Exit if trend weakens
    df["sell"] = (df["Close"] < df["MA50"]) | (df["RSI"] < 45)

    for _, row in df.iterrows():
        price = row["Close"]

        if position == 0 and row["buy"]:
            position = 1
            entry_price = price

        elif position == 1 and row["sell"]:
            profit = (price - entry_price) / entry_price
            trades.append(profit)
            position = 0

    return calc_stats(ticker, "Pullback", trades)


if run_button:
    results = []

    for ticker in TICKERS:
        st.write(f"Running {ticker}...")

        df = download_data(ticker)

        if df is None:
            continue

        trend_result = trend_strategy(ticker, df.copy())
        pullback_result = pullback_strategy(ticker, df.copy())

        if trend_result:
            results.append(trend_result)

        if pullback_result:
            results.append(pullback_result)

    results_df = pd.DataFrame(results)

    if not results_df.empty:
        st.subheader("📈 All Strategy Results")
        st.dataframe(results_df)

        st.subheader("🔥 Best Strategy Per Stock")

        best_per_stock = (
            results_df.sort_values("Ranking Score", ascending=False)
            .groupby("Ticker")
            .head(1)
            .sort_values("Ranking Score", ascending=False)
        )

        st.dataframe(best_per_stock)

        st.subheader("🚗 TSLA Strategy Comparison")
        tsla_results = results_df[results_df["Ticker"] == "TSLA"]

        if not tsla_results.empty:
            st.dataframe(tsla_results)
        else:
            st.write("No TSLA results found.")
    else:
        st.write("No valid results.")