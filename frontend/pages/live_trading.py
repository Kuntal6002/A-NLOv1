# frontend/pages/live_trading.py - AI Trading Dashboard
import streamlit as st
import os
import sys
from pathlib import Path
import pandas as pd

# Load .env first
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except:
    pass

# Fix Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.alpaca_mcp import AlpacaMCP
from agents.llm_trader import LLMTrader

def init_trader():
    """Initialize trader once"""
    if "trader_initialized" not in st.session_state:
        api_key = os.getenv('ALPACA_API_KEY', 'PKJQ4MG6LRX3YQWXHPUSBJ72UR')
        secret_key = os.getenv('ALPACA_SECRET_KEY', 'ERPjEteCfxbwhn1uEDoKGnQjNxksehTYGCvqmMZ6qEJZ')

        mcp = AlpacaMCP(api_key, secret_key, paper=True)
        trader = LLMTrader(mcp)

        st.session_state.trader = trader
        st.session_state.mcp = mcp
        st.session_state.trader_initialized = True

    return st.session_state.trader, st.session_state.mcp

def update_status(mcp):
    """Fetch fresh account data"""
    try:
        acct = mcp.get_account()
        positions = mcp.get_all_positions()
        st.session_state.status = {"account": acct, "positions": positions}
        return True
    except Exception as e:
        st.error(f"Status error: {e}")
        return False

def show_status():
    """Display account metrics and positions"""
    status = st.session_state.get("status", {"account": {}, "positions": []})
    acct = status["account"]

    if acct.get("success"):
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Equity", f"${float(acct.get('equity', 0)):,.0f}")
        col2.metric("💵 Cash", f"${float(acct.get('cash', 0)):,.0f}")
        col3.metric("⚡ Buying Power", f"${float(acct.get('buying_power', 0)):,.0f}")

        positions = status["positions"]
        if positions:
            st.subheader("📊 Open Positions")
            df = pd.DataFrame(positions)
            st.dataframe(df[["symbol", "qty", "market_value", "unrealized_pl"]],
                        height=200, use_container_width=True)
        else:
            st.info("📭 No open positions")
    else:
        st.warning("⚠️ Click refresh to load account data")

def render(api):
    st.title("🤖 AI Paper Trading")
    st.caption("*Paper trading with $100K virtual account - Powered by Groq AI*")

    # Initialize trader
    trader, mcp = init_trader()

    # Layout
    col1, col2 = st.columns([2, 1])

    # === LEFT COLUMN: Status ===
    with col1:
        if st.button("🔄 Refresh Account", type="secondary", use_container_width=True):
            with st.spinner("Refreshing..."):
                if update_status(mcp):
                    st.success("✅ Updated!")

        # Initialize status on first load
        if "status" not in st.session_state:
            update_status(mcp)

        show_status()

    # === RIGHT COLUMN: Trading ===
    with col2:
        # Quick Trade Section
        st.subheader("⚡ Quick Trade")

        # Input fields with UNIQUE keys
        trade_symbol = st.text_input("Symbol", "AAPL", key="trade_symbol_input")
        trade_qty = st.number_input("Shares", 1, 100, 1, key="trade_qty_input")

        # Buy/Sell buttons
        col_buy, col_sell = st.columns(2)

        with col_buy:
            if st.button("🟢 BUY", type="primary", use_container_width=True, key="buy_btn"):
                with st.spinner(f"Buying {trade_qty} {trade_symbol}..."):
                    result = trader.process_command(f"buy {trade_qty} {trade_symbol}")

                    if result.get("success"):
                        st.success(f"✅ Bought {trade_qty} {trade_symbol}!")
                        st.balloons()
                        update_status(mcp)
                        st.rerun()
                    else:
                        st.error(f"❌ {result.get('message', 'Failed')}")

        with col_sell:
            if st.button("🔴 SELL", type="secondary", use_container_width=True, key="sell_btn"):
                with st.spinner(f"Selling {trade_qty} {trade_symbol}..."):
                    result = trader.process_command(f"sell {trade_qty} {trade_symbol}")

                    if result.get("success"):
                        st.success(f"✅ Sold {trade_qty} {trade_symbol}!")
                        update_status(mcp)
                        st.rerun()
                    else:
                        st.error(f"❌ {result.get('message', 'Failed')}")

        st.divider()

        # AI Chat Section
        st.subheader("🧠 AI Assistant")

        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Chat input
        user_msg = st.chat_input("💬 Ask AI: 'Buy 10 AAPL' or 'Portfolio status?'")

        if user_msg:
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": user_msg})

            # Process with AI
            with st.spinner("🤖 AI thinking..."):
                result = trader.process_command(user_msg)

                ai_msg = {
                    "role": "assistant",
                    "content": result.get('message', 'Processing...'),
                    "reasoning": result.get('ai_reasoning', ''),
                    "success": result.get('success', False)
                }
                st.session_state.chat_history.append(ai_msg)

                # Update status if trade was made
                if result.get('action') in ['buy', 'sell']:
                    update_status(mcp)

            st.rerun()

        # Display chat history
        chat_container = st.container(height=350)
        with chat_container:
            for msg in st.session_state.chat_history[-8:]:  # Last 8 messages
                if msg["role"] == "user":
                    st.chat_message("user").markdown(f"**You:** {msg['content']}")
                else:
                    icon = "✅" if msg.get("success") else "⚠️"
                    st.chat_message("assistant").markdown(
                        f"**AI:** {msg['content']} {icon}\n\n"
                        f"*{msg.get('reasoning', 'N/A')}*"
                    )

        # Clear chat button
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat_btn"):
                st.session_state.chat_history = []
                st.rerun()
