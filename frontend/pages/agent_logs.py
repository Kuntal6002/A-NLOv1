# frontend/pages/agent_logs.py
import streamlit as st
import pandas as pd


def render(api):
    st.title("🤖 Agent Logs")

    logs = api("/logs")
    if not logs:
        st.info("No agent cycles yet. Run a cycle from the Overview page.")
        return

    df = pd.DataFrame(
        [
            {
                "cycle": l["cycle"],
                "timestamp": l["timestamp"],
                "action": l["plan"].get("action", ""),
                "amount": l["plan"].get("invest_amount", 0.0),
                "mode": l["plan"].get("invest_mode", ""),
                "ticker": l["plan"].get("ticker", ""),
                "reward": l["reward"],
            }
            for l in logs
        ]
    )

    st.subheader("Timeline")
    st.dataframe(df, use_container_width=True, height=350)

    st.subheader("Details")
    sel_cycle = st.number_input(
        "Select cycle", min_value=int(df["cycle"].min()), max_value=int(df["cycle"].max())
    )
    row = next((l for l in logs if l["cycle"] == sel_cycle), None)
    if row:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**State**")
            st.json(row["state"])
            st.markdown("**Plan**")
            st.json(row["plan"])
        with c2:
            st.markdown("**Result**")
            st.json(row["result"])
            st.markdown("**Reward**")
            st.code(f"{row['reward']:.3f}")
