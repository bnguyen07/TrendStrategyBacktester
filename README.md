# 📊 Trend Strategy Backtester

A multi-strategy stock backtesting app built with Streamlit.

## 🚀 Features

- Trend strategy
- Pullback strategy
- Multi-stock backtesting
- Ranking system (best strategy per stock)
- Clean UI

## 🧠 Strategies

### Trend Strategy
- Buy in strong uptrend
- Uses MA50, MA200, RSI

### Pullback Strategy
- Buy after pullback + breakout
- Designed for volatile stocks like TSLA, NVDA

## 🖥️ Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
