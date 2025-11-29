# frontend/pages/overview.py
import streamlit as st
import pandas as pd
import altair as alt


PRIMARY = "#00b386"
DANGER = "#ff4d4f"


def _growth_badge(value: float) -> str:
    arrow = "▲" if value >= 0 else "▼"
    color = PRIMARY if value >= 0 else DANGER
    return f"<span style='color:{color}; font-weight:600;'>{arrow} {value:.2f}%</span>"


def render(api):
    st.title("Portfolio Overview")

    state = api("/state")
    portfolio = api("/portfolio")
    market = api("/market")
    logs = api("/logs")

    total_value = portfolio["value"]
    invested_amount = portfolio["invested_amount"]
    profit_abs = portfolio["absolute_profit_loss"]
    profit_pct = portfolio["percentage_profit_loss"]
    today_pl = portfolio["daily_profit_loss"]
    today_pl_base = total_value - today_pl if total_value > today_pl else total_value
    today_pl_pct = (today_pl / today_pl_base * 100.0) if today_pl_base > 0 else 0.0

    sip_suggested = state.get("sip_suggested_amount", portfolio.get("sip_suggested_amount", 0.0))

    if "last_sip_suggestion" not in st.session_state:
        st.session_state["last_sip_suggestion"] = sip_suggested
    delta_sip = sip_suggested - st.session_state["last_sip_suggestion"]
    st.session_state["last_sip_suggestion"] = sip_suggested
    sip_delta_pct = (delta_sip / abs(sip_suggested) * 100.0) if sip_suggested else 0.0

    st.markdown(
        """
        <style>
        .anlo-card {
            background: radial-gradient(circle at top left, #1f2937 0, #020617 60%);
            border-radius: 16px;
            padding: 16px 20px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.35);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown('<div class="anlo-card">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown("**Total Portfolio Value**")
        c1.markdown(f"₹ {total_value:,.2f}")
        c2.markdown("**Invested Amount**")
        c2.markdown(f"₹ {invested_amount:,.2f}")
        c3.markdown("**Profit / Loss**")
        c3.markdown(f"₹ {profit_abs:,.2f}")
        c3.markdown(_growth_badge(profit_pct), unsafe_allow_html=True)
        c4.markdown("**Today’s P/L**")
        c4.markdown(f"₹ {today_pl:,.2f}")
        c4.markdown(_growth_badge(today_pl_pct), unsafe_allow_html=True)
        c5.markdown("**Suggested SIP**")
        c5.markdown(f"₹ {sip_suggested:,.2f}")
        c5.markdown(_growth_badge(sip_delta_pct), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    left, right = st.columns([3, 2], gap="large")

    # ---- Left: Portfolio Analytics ----
    with left:
        st.subheader("Portfolio Analytics")

        bank_balance = state["bank_balance"]
        positions = portfolio.get("positions", {}) or {}
        current_price = market["current_price"]

        eq_value = sum(units * current_price for t, units in positions.items())
        sip_total = sum(market["sip_history"]) if market["sip_history"] else 0.0
        cash_value = bank_balance

        alloc_data = [
            {"asset": "Equity / Index", "value": eq_value},
            {"asset": "SIP", "value": sip_total},
            {"asset": "Cash", "value": cash_value},
        ]
        df_alloc = pd.DataFrame(alloc_data)
        df_alloc = df_alloc[df_alloc["value"] > 0]

        if not df_alloc.empty:
            chart_alloc = (
                alt.Chart(df_alloc)
                .mark_arc(outerRadius=110)
                .encode(theta="value:Q", color="asset:N")
            )
            st.altair_chart(chart_alloc, use_container_width=True)

        income_hist = market["income_history"]
        expense_hist = market["expense_history"]
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
            st.subheader("Net Inflow / Outflow")
            chart_flow = (
                alt.Chart(df_m)
                .mark_bar()
                .encode(x="step:O", y="amount:Q", color="type:N")
                .properties(height=260)
            )
            st.altair_chart(chart_flow, use_container_width=True)

    # ---- Right: Agent Insights ----
    with right:
        st.subheader("Agent Insights")

        last_log = logs[-1] if logs else None
        if not last_log:
            st.info("No agent cycles yet. Run a cycle to see insights.")
        else:
            plan = last_log["plan"]
            s2 = last_log["state"]

            with st.expander("Trading Bot", expanded=True):
                st.write("**Signal**:", plan.get("signal", "").upper())
                st.write("**Confidence**:", f"{plan.get('signal_confidence', 0)} %")
                vol = s2.get("volatility", 0.0)
                if vol < 0.02:
                    vlabel = "Low"
                elif vol < 0.04:
                    vlabel = "Medium"
                else:
                    vlabel = "High"
                st.write("**Volatility**:", f"{vlabel} ({vol:.3f})")

            with st.expander("SIP Engine & Opportunity"):
                st.write("**Suggested SIP**:", f"₹ {plan.get('suggested_sip', 0.0):.2f}")
                st.write("**Mode**:", plan.get("invest_mode", "sip").upper())
                st.write("**Ticker**:", plan.get("ticker", "INDEX"))
                st.write("**Action**:", plan.get("action", "").upper())

            with st.expander("Risk & Safety"):
                st.write("**Emergency buffer OK**:", s2.get("emergency_buffer_ok", True))
                st.write("**Bank Balance**:", f"₹ {s2.get('bank_balance', 0.0):.2f}")
                st.write("**Emergency Buffer Need**:", f"₹ {s2.get('emergency_buffer', 0.0):.2f}")
                st.write("**Risk Profile**:", s2.get("risk_profile", "balanced").title())

    st.write("")
    if st.button("Run AI Cycle", use_container_width=True):
        api("/run_cycle", method="POST")
        st.rerun()
