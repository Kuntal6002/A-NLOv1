# frontend/pages/investments.py
import streamlit as st
import pandas as pd
import altair as alt
import math


def _compute_holdings_table(port, market):
    positions = port.get("positions", {}) or {}
    price = market["current_price"]
    rows = []
    total_value = 0.0
    for t, units in positions.items():
        curr_val = units * price
        invested = curr_val  # if you later track cost basis, replace here
        abs_pl = curr_val - invested
        daily_pl = 0.0
        rows.append(
            {
                "Ticker": t,
                "Current Value": curr_val,
                "Invested Amount": invested,
                "Absolute P/L": abs_pl,
                "Daily P/L": daily_pl,
                "Quantity": units,
                "Avg Buy Price": price,
            }
        )
        total_value += curr_val

    for r in rows:
        r["Allocation %"] = (
            r["Current Value"] / total_value * 100.0 if total_value > 0 else 0.0
        )

    return pd.DataFrame(rows)


def _simple_drawdown(nav_hist):
    if not nav_hist:
        return 0.0
    peak = nav_hist[0]
    max_dd = 0.0
    for v in nav_hist:
        peak = max(peak, v)
        dd = (v - peak) / peak if peak > 0 else 0.0
        max_dd = min(max_dd, dd)
    return max_dd


def render(api):
    st.title("Investments")

    port = api("/portfolio")
    market = api("/market")
    logs = api("/logs")

    tabs = st.tabs(["Holdings", "SIPs", "Lump-sum", "Transactions", "Watchlist"])

    # --- Holdings ---
    with tabs[0]:
        df_hold = _compute_holdings_table(port, market)
        if not df_hold.empty:
            sort_col = st.selectbox(
                "Sort by",
                ["Ticker", "Current Value", "Invested Amount", "Absolute P/L", "Allocation %"],
                index=1,
            )
            df_disp = df_hold.sort_values(sort_col, ascending=False)
            st.dataframe(df_disp, use_container_width=True)
        else:
            st.info("No holdings yet. Run a few AI cycles to start investing.")

    # --- SIPs: separate graph ONLY for SIP contributions ---
    with tabs[1]:
        st.subheader("SIP Contributions Over Time")
        sip_hist = market["sip_history"]

        if sip_hist:
            df_sip = pd.DataFrame(
                {"cycle": range(len(sip_hist)), "sip_amount": sip_hist}
            )
            st.dataframe(df_sip, use_container_width=True, height=220)
            chart_sip = (
                alt.Chart(df_sip)
                .mark_line(color="#00b386", point=True)
                .encode(x="cycle:Q", y="sip_amount:Q")
                .properties(height=260)
            )
            st.altair_chart(chart_sip, use_container_width=True)
        else:
            st.info("No SIPs executed yet. The agent will create SIPs as conditions allow.")

    # --- Lump-sum: separate graph ONLY for lump-sum actions ---
    with tabs[2]:
        st.subheader("Lump-sum Investments Over Time")
        lump_hist = market["lumpsum_history"]

        if lump_hist:
            df_lump = pd.DataFrame(
                {"cycle": range(len(lump_hist)), "lumpsum_amount": lump_hist}
            )
            st.dataframe(df_lump, use_container_width=True, height=220)
            chart_lump = (
                alt.Chart(df_lump)
                .mark_bar(color="#f97316")
                .encode(x="cycle:Q", y="lumpsum_amount:Q")
                .properties(height=260)
            )
            st.altair_chart(chart_lump, use_container_width=True)
        else:
            st.info("No lump-sum investments yet. They trigger only on strong BUY signals.")

    # --- Transactions ---
    with tabs[3]:
        txs = api("/transactions")
        df_tx = pd.DataFrame(txs) if txs else pd.DataFrame()
        st.subheader("Transactions")
        st.dataframe(df_tx, use_container_width=True, height=350)

    # --- Watchlist (simple INDEX watch) ---
    with tabs[4]:
        st.subheader("Watchlist")
        st.write("INDEX (simulated)")
        price_hist = market["price_history"]
        if price_hist:
            df_price = pd.DataFrame({"step": range(len(price_hist)), "price": price_hist})
            chart_p = (
                alt.Chart(df_price)
                .mark_line(color="#0ea5e9")
                .encode(x="step:Q", y="price:Q")
                .properties(height=260)
            )
            st.altair_chart(chart_p, use_container_width=True)
        else:
            st.info("No price history yet. Run a cycle to start the market simulation.")

    # --- Advanced analytics at bottom of page ---
    st.write("---")
    st.subheader("Advanced Analytics")

    nav_hist = market["nav_history"]
    if nav_hist:
        df_nav = pd.DataFrame({"step": range(len(nav_hist)), "nav": nav_hist})
        c1, c2 = st.columns(2)
        with c1:
            st.write("Portfolio Growth (NAV)")
            chart_nav = (
                alt.Chart(df_nav)
                .mark_line(color="#00b386")
                .encode(x="step:Q", y="nav:Q")
                .properties(height=260)
            )
            st.altair_chart(chart_nav, use_container_width=True)

        with c2:
            base = nav_hist[0]
            df_pl = pd.DataFrame(
                {"step": range(len(nav_hist)), "pl": [v - base for v in nav_hist]}
            )
            st.write("Profit / Loss Timeline")
            chart_pl = (
                alt.Chart(df_pl)
                .mark_line(color="#f97316")
                .encode(x="step:Q", y="pl:Q")
                .properties(height=260)
            )
            st.altair_chart(chart_pl, use_container_width=True)

        # Rolling volatility
        rets = []
        for i in range(1, len(nav_hist)):
            if nav_hist[i - 1] > 0:
                rets.append((nav_hist[i] - nav_hist[i - 1]) / nav_hist[i - 1])
        roll = []
        win = 5
        for i in range(len(rets)):
            window = rets[max(0, i - win + 1) : i + 1]
            if window:
                mu = sum(window) / len(window)
                var = sum((r - mu) ** 2 for r in window) / len(window)
                roll.append(math.sqrt(var))
            else:
                roll.append(0.0)
        df_vol = pd.DataFrame({"step": range(1, len(nav_hist)), "vol": roll})
        st.write("Rolling Volatility (NAV)")
        chart_vol = (
            alt.Chart(df_vol)
            .mark_line(color="#eab308")
            .encode(x="step:Q", y="vol:Q")
            .properties(height=260)
        )
        st.altair_chart(chart_vol, use_container_width=True)

        avg_ret = sum(rets) / len(rets) if rets else 0.0
        vol_total = (
            (sum((r - avg_ret) ** 2 for r in rets) / len(rets)) ** 0.5 if rets else 0.0
        )
        sharpe = (avg_ret / vol_total * (252 ** 0.5)) if vol_total > 0 else 0.0
        max_dd = _simple_drawdown(nav_hist)

        m1, m2, m3 = st.columns(3)
        m1.metric("Sharpe (approx)", f"{sharpe:.2f}")
        m2.metric("Max Drawdown", f"{max_dd*100:.2f}%")
        m3.metric("Beta (mock)", "1.00")
    else:
        st.info("NAV history is empty. Run a few cycles to populate analytics.")
