# backend/utils.py
import json
import random
from typing import Any, Dict, List

from . import database as db
from agents_investment.investment_agent import (
    get_portfolio_value,
    get_positions,
    buy as portfolio_buy,
    evaluate_investment_opportunity,
)
from agents_investment.market_generator import get_index_metrics


SIM_STATE: Dict[str, Any] = {
    "bank_balance": 10000.0,
    "base_income": 5000.0,
    "base_expense": 3000.0,
    "income_history": [],
    "expense_history": [],
    "balance_history": [10000.0],
    "sip_history": [],
    "lumpsum_history": [],
    "nav_history": [],
    "invested_amount": 0.0,
    "last_sip_suggested": 0.0,
}


def reset_sim_state() -> None:
    SIM_STATE["bank_balance"] = 10000.0
    SIM_STATE["income_history"] = []
    SIM_STATE["expense_history"] = []
    SIM_STATE["balance_history"] = [SIM_STATE["bank_balance"]]
    SIM_STATE["sip_history"] = []
    SIM_STATE["lumpsum_history"] = []
    SIM_STATE["nav_history"] = []
    SIM_STATE["invested_amount"] = 0.0
    SIM_STATE["last_sip_suggested"] = 0.0


def _persist_balance(timestamp: str) -> None:
    date = (timestamp.split("T")[0] if "T" in timestamp else timestamp) or "1970-01-01"
    db.execute(
        "INSERT OR REPLACE INTO balances (date, balance) VALUES (?, ?)",
        (date, float(SIM_STATE["bank_balance"])),
    )


def _log_transaction(
    timestamp: str, ttype: str, amount: float, description: str, category: str = ""
) -> None:
    """
    Store transaction in SQLite, embedding balance_after into description.
    """
    bal = SIM_STATE["bank_balance"]
    desc = f"{description} | balance_after={bal:.2f}"
    db.execute(
        """
        INSERT INTO transactions (date, type, category, amount, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (timestamp, ttype, category, float(amount), desc),
    )


def get_transactions() -> List[Dict[str, Any]]:
    rows = db.fetch_all(
        "SELECT id, date, type, category, amount, description "
        "FROM transactions ORDER BY date ASC, id ASC"
    )
    out: List[Dict[str, Any]] = []
    for r in rows:
        bal_after = None
        desc = r.get("description") or ""
        marker = "balance_after="
        if marker in desc:
            try:
                bal_after = float(desc.split(marker)[-1].split()[0])
            except Exception:
                bal_after = None
        out.append(
            {
                "id": r["id"],
                "timestamp": r["date"],
                "type": r["type"],
                "category": r["category"],
                "amount": float(r["amount"]),
                "description": desc,
                "balance_after": bal_after,
            }
        )
    return out


def _construct_core_state() -> Dict[str, Any]:
    price_history, current_price, vol, ret = get_index_metrics()
    nav_holdings = get_portfolio_value()
    bank_balance = float(SIM_STATE["bank_balance"])

    income_hist: List[float] = SIM_STATE["income_history"]
    expense_hist: List[float] = SIM_STATE["expense_history"]
    monthly_income = float(income_hist[-1]) if income_hist else 0.0
    monthly_expense = float(expense_hist[-1]) if expense_hist else 0.0
    emergency_buffer = monthly_expense * 3.0 if monthly_expense > 0 else 0.0
    emergency_ok = bank_balance >= emergency_buffer

    if vol < 0.02:
        risk_profile = "aggressive"
    elif vol < 0.035:
        risk_profile = "balanced"
    else:
        risk_profile = "conservative"

    total_portfolio_value = bank_balance + nav_holdings

    core = {
        "balance": bank_balance,
        "income_rate": monthly_income,
        "expense_rate": monthly_expense,
        "volatility": vol,
        "portfolio_value": total_portfolio_value,
        "emergency_buffer_ok": emergency_ok,
        "risk_profile": risk_profile,
        "bank_balance": bank_balance,
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "emergency_buffer": emergency_buffer,
        "price_history": price_history,
        "nav_history": SIM_STATE["nav_history"],
    }
    return core


def _recompute_sip_suggestion(state_for_agent: Dict[str, Any]) -> float:
    rec = evaluate_investment_opportunity(state_for_agent) or {}
    sip = float(rec.get("sip_suggested_amount", rec.get("amount", 0.0) or 0.0))
    SIM_STATE["last_sip_suggested"] = sip
    return sip


def simulate_income_and_expense(timestamp: str) -> Dict[str, float]:
    base_inc = float(SIM_STATE["base_income"])
    base_exp = float(SIM_STATE["base_expense"])

    income = max(0.0, random.gauss(base_inc, 0.3 * base_inc))
    expense = max(0.0, random.gauss(base_exp, 0.2 * base_exp))

    SIM_STATE["bank_balance"] += income
    SIM_STATE["income_history"].append(income)
    _log_transaction(timestamp, "income", income, "unstable income", "income")

    SIM_STATE["bank_balance"] -= expense
    SIM_STATE["expense_history"].append(expense)
    _log_transaction(timestamp, "expense", expense, "variable expense", "expense")

    SIM_STATE["balance_history"].append(SIM_STATE["bank_balance"])
    _persist_balance(timestamp)

    core = _construct_core_state()
    _recompute_sip_suggestion(core)

    return {"monthly_income": income, "monthly_expense": expense}


def apply_investment(
    timestamp: str, mode: str, ticker: str, amount: float
) -> Dict[str, Any]:
    amount = max(0.0, float(amount))
    if amount <= 0.0:
        SIM_STATE["sip_history"].append(0.0)
        SIM_STATE["lumpsum_history"].append(0.0)
        return {"status": "noop", "amount": 0.0}

    invest_amt = min(amount, SIM_STATE["bank_balance"])
    SIM_STATE["bank_balance"] -= invest_amt

    if mode == "lumpsum":
        SIM_STATE["sip_history"].append(0.0)
        SIM_STATE["lumpsum_history"].append(invest_amt)
        _log_transaction(timestamp, "lumpsum", invest_amt, "lump-sum investment", "invest")
    else:
        SIM_STATE["sip_history"].append(invest_amt)
        SIM_STATE["lumpsum_history"].append(0.0)
        _log_transaction(timestamp, "sip", invest_amt, "SIP investment", "invest")

    trade_result = portfolio_buy(ticker, invest_amt)
    _log_transaction(
        timestamp,
        "portfolio_buy",
        invest_amt,
        f"Portfolio buy {ticker}",
        "portfolio",
    )

    SIM_STATE["balance_history"].append(SIM_STATE["bank_balance"])
    SIM_STATE["invested_amount"] += invest_amt
    _persist_balance(timestamp)

    core = _construct_core_state()
    _recompute_sip_suggestion(core)

    return trade_result


def insert_transaction(tx: Dict[str, Any]) -> None:
    """
    Insert a user-created transaction and keep SIM_STATE.bank_balance in sync.
    Called by POST /transactions and the Cashflow form.
    """
    timestamp = tx.get("date") or tx.get("timestamp") or ""
    amount = float(tx.get("amount", 0.0))
    ttype = (tx.get("type") or "manual").lower()
    category = tx.get("category", "")
    desc = tx.get("description", "manual")

    if ttype == "income":
        SIM_STATE["bank_balance"] += amount
        SIM_STATE["income_history"].append(amount)
    elif ttype in ("expense", "repay"):
        SIM_STATE["bank_balance"] -= amount
        SIM_STATE["expense_history"].append(amount)

    SIM_STATE["balance_history"].append(SIM_STATE["bank_balance"])
    _persist_balance(timestamp)
    _log_transaction(timestamp, ttype, amount, desc, category)

    core = _construct_core_state()
    _recompute_sip_suggestion(core)


def update_nav_history() -> float:
    nav = get_portfolio_value()
    SIM_STATE["nav_history"].append(nav)
    return nav


def get_state() -> Dict[str, Any]:
    core = _construct_core_state()
    _recompute_sip_suggestion(core)
    core["sip_suggested_amount"] = SIM_STATE["last_sip_suggested"]
    core["cashflow_inflow"] = float(sum(SIM_STATE["income_history"]))
    core["cashflow_outflow"] = float(sum(SIM_STATE["expense_history"]))
    return core


def get_portfolio() -> Dict[str, Any]:
    positions = get_positions()
    nav_holdings = get_portfolio_value()
    cash = float(SIM_STATE["bank_balance"])
    total_value = cash + nav_holdings

    invested_amount = float(SIM_STATE["invested_amount"])
    abs_pl = total_value - invested_amount
    pct_pl = (abs_pl / invested_amount * 100.0) if invested_amount > 0 else 0.0

    nav_hist = SIM_STATE["nav_history"]
    if len(nav_hist) >= 2:
        daily_pl = nav_hist[-1] - nav_hist[-2]
    else:
        daily_pl = 0.0

    return {
        "cash": cash,
        "positions": positions,
        "value": total_value,
        "invested_amount": invested_amount,
        "absolute_profit_loss": abs_pl,
        "percentage_profit_loss": pct_pl,
        "daily_profit_loss": daily_pl,
        "sip_suggested_amount": SIM_STATE["last_sip_suggested"],
        "cashflow_inflow": float(sum(SIM_STATE["income_history"])),
        "cashflow_outflow": float(sum(SIM_STATE["expense_history"])),
    }


def get_logs() -> List[Dict[str, Any]]:
    rows = db.fetch_all(
        "SELECT cycle, timestamp, state, plan, result, reward "
        "FROM agent_logs ORDER BY cycle ASC"
    )
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "cycle": int(r["cycle"]),
                "timestamp": r["timestamp"],
                "state": json.loads(r["state"]),
                "plan": json.loads(r["plan"]),
                "result": json.loads(r["result"]),
                "reward": float(r["reward"]),
            }
        )
    return out


def get_market() -> Dict[str, Any]:
    price_history, current_price, vol, ret = get_index_metrics()
    return {
        "price_history": [float(x) for x in price_history],
        "current_price": float(current_price),
        "volatility": float(vol),
        "return_rate": float(ret),
        "nav_history": [float(x) for x in SIM_STATE["nav_history"]],
        "sip_history": [float(x) for x in SIM_STATE["sip_history"]],
        "lumpsum_history": [float(x) for x in SIM_STATE["lumpsum_history"]],
        "income_history": [float(x) for x in SIM_STATE["income_history"]],
        "expense_history": [float(x) for x in SIM_STATE["expense_history"]],
        "balance_history": [float(x) for x in SIM_STATE["balance_history"]],
    }


def store_run_cycle_output(
    state: Dict[str, Any],
    plan: Dict[str, Any],
    result: Dict[str, Any],
    reward: float,
    timestamp: str,
) -> int:
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO agent_logs (timestamp, state, plan, result, reward)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            json.dumps(state),
            json.dumps(plan),
            json.dumps(result),
            float(reward),
        ),
    )
    cycle_id = cur.lastrowid

    bal = state.get("bank_balance", state.get("balance", 0.0))
    cur.execute(
        "INSERT OR REPLACE INTO balances (date, balance) VALUES (?, ?)",
        (timestamp.split("T")[0], float(bal)),
    )

    conn.commit()
    conn.close()
    return cycle_id
