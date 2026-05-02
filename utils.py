import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

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
