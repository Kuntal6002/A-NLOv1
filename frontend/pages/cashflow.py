# frontend/pages/cashflow.py
import time

import streamlit as st
import pandas as pd
import altair as alt


def render(api):
    st.title("Cash Flow")

    txs = api("/transactions")
    df = pd.DataFrame(txs) if txs else pd.DataFrame(
        columns=["id", "timestamp", "type", "category", "amount", "description", "balance_after"]
    )

    state = api("/state")
    market = api("/market")
    bank_balance = state["bank_balance"]
    emergency = state["emergency_buffer"]
    suggested_sip = state.get("sip_suggested_amount", 0.0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Available Cash", f"₹ {bank_balance:,.2f}")
    c2.metric("Emergency Buffer", f"₹ {emergency:,.2f}")
    c3.metric("Suggested SIP (live)", f"₹ {suggested_sip:,.2f}")

    st.subheader("Transactions")
    st.dataframe(df, use_container_width=True, height=280)

    with st.expander("Add Manual Transaction"):
        date = st.date_input("Date")
        ttype = st.selectbox("Type", ["income", "expense"])
        category = st.text_input("Category", "general")
        amount = st.number_input("Amount", min_value=0.0, value=100.0, step=10.0)
        desc = st.text_input("Description", "")

        if "saving_tx" not in st.session_state:
            st.session_state["saving_tx"] = False

        disabled = st.session_state["saving_tx"]
        if st.button("Save Transaction", disabled=disabled):
            st.session_state["saving_tx"] = True
            with st.spinner("Saving transaction..."):
                api(
                    "/transactions",
                    method="POST",
                    json={
                        "date": str(date),
                        "type": ttype,
                        "category": category,
                        "amount": amount,
                        "description": desc,
                    },
                )
                time.sleep(0.5)
            st.success("Transaction added successfully!")
            st.session_state["saving_tx"] = False
            st.rerun()

    income_hist = market["income_history"]
    expense_hist = market["expense_history"]
    balance_hist = market["balance_history"]

    if income_hist and expense_hist:
        steps = list(range(max(len(income_hist), len(expense_hist))))
        df_flow = pd.DataFrame(
            {
                "step": steps,
                "Inflow": income_hist + [0.0] * (len(steps) - len(income_hist)),
                "Outflow": expense_hist + [0.0] * (len(steps) - len(expense_hist)),
            }
        )
        df_m = df_flow.melt(id_vars="step", var_name="type", value_name="amount")
        st.subheader("Monthly Inflow / Outflow")
        chart = (
            alt.Chart(df_m)
            .mark_bar()
            .encode(x="step:O", y="amount:Q", color="type:N")
            .properties(height=260)
        )
        st.altair_chart(chart, use_container_width=True)

    if balance_hist:
        st.subheader("Running Cash Balance")
        df_b = pd.DataFrame({"step": range(len(balance_hist)), "balance": balance_hist})
        chart_b = (
            alt.Chart(df_b)
            .mark_line()
            .encode(x="step:Q", y="balance:Q")
            .properties(height=260)
        )
        st.altair_chart(chart_b, use_container_width=True)
