# frontend/app.py
import streamlit as st
import requests
from pages import overview, cashflow, agent_logs, investments

# Import live_trading with error handling
try:
    from pages import live_trading
    LIVE_TRADING_AVAILABLE = True
except ImportError as e:
    LIVE_TRADING_AVAILABLE = False
    LIVE_TRADING_ERROR = str(e)

API_BASE = "http://localhost:8000"

def api(endpoint: str, method: str = "GET", json=None):
    url = API_BASE + endpoint
    if method.upper() == "GET":
        r = requests.get(url, timeout=5)
    else:
        r = requests.post(url, json=json, timeout=5)
    r.raise_for_status()
    return r.json()

def main():
    st.set_page_config(
        page_title="A-NLO — Adaptive Neural Life Orchestrator",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        body { background-color: #02040A; }
        .block-container { padding-top: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("A-NLO Dashboard")

    # Build navigation menu dynamically
    nav_options = ["Overview", "Cashflow", "Agent Logs", "Investments"]

    if LIVE_TRADING_AVAILABLE:
        nav_options.append("Paper Trading")

    page = st.sidebar.radio(
        "Navigate",
        nav_options,
        index=0,
    )

    # Show warning if Paper Trading is unavailable
    if not LIVE_TRADING_AVAILABLE and st.sidebar.checkbox("ℹ️ Show Debug Info", False):
        st.sidebar.warning(f"Paper Trading module unavailable: {LIVE_TRADING_ERROR}")

    # Route to pages
    if page == "Overview":
        overview.render(api)
    elif page == "Cashflow":
        cashflow.render(api)
    elif page == "Agent Logs":
        agent_logs.render(api)
    elif page == "Investments":
        investments.render(api)
    elif page == "Paper Trading":
        if LIVE_TRADING_AVAILABLE:
            live_trading.render(api)
        else:
            st.error("❌ Paper Trading module is not available")
            st.info("Required files: pages/live_trading.py, agents/alpaca_mcp.py, agents/llm_trader.py")

if __name__ == "__main__":
    main()
