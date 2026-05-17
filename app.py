import streamlit as st

st.set_page_config(page_title="Welcome", layout="wide")

st.title("Welcome to Trend Strategy Backtester")
st.write("Please select a page from the sidebar to continue, or use the links below.")

st.page_link("pages/1_Backtester.py", label="Backtester", icon="📊")
st.page_link("pages/2_Signal_Scanner.py", label="Signal Scanner", icon="🚨")
st.page_link("pages/3_Terms_and_Conditions.py", label="Terms and Conditions", icon="📄")
