import streamlit as st

st.set_page_config(page_title="Terms & Conditions", layout="wide")

st.sidebar.title("📊 Navigation")
st.sidebar.markdown("""
- Backtester
- Signal Scanner
- Terms & Conditions
""")

st.title("📄 Terms & Conditions")

st.markdown("""
### ⚠️ Important Disclaimer
This application is provided for **educational and informational purposes only** and does **not constitute financial, investment, or trading advice**.

---

### 📊 Risk Disclosure
Trading and investing involve **substantial risk**, including:
- Loss of capital
- Market volatility
- Unpredictable outcomes

Past performance does **NOT** guarantee future results.

---

### ❗ No Liability
By using this application, you agree that:
- You are **fully responsible** for your own trading decisions  
- The author is **NOT liable** for any financial losses or damages  
- No guarantee is made regarding accuracy or profitability  

---

### 🧠 Use at Your Own Risk
This tool is a **research and learning tool only**.
You should always:
- Do your own research (DYOR)
- Consult a licensed financial advisor

---

### ✅ Acceptance of Terms
By continuing to use this application, you acknowledge that:
✔ You understand the risks  
✔ You accept full responsibility  
✔ You agree to these terms  

---

### 📬 Contact
For questions, please contact the developer.
---
""")

st.success("✔ You are responsible for your own financial decisions.")
