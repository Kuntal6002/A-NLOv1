# agents_core/planner.py
from typing import Dict, Any

from agents_investment.investment_agent import evaluate_investment_opportunity


def plan(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Planner uses evaluate_investment_opportunity() to decide actions
    and also passes through the suggested SIP amount for the UI.
    """
    inv = evaluate_investment_opportunity(state)

    action = "hold"
    invest_amount = 0.0
    invest_mode = "sip"
    ticker = "INDEX"

    if inv["should_invest"]:
        action = "invest"
        invest_amount = float(inv["amount"])
        invest_mode = inv["mode"]
        ticker = inv["ticker"]
    else:
        if not state.get("emergency_buffer_ok", True):
            action = "save"
        elif state.get("expense_rate", 0.0) > state.get("income_rate", 0.0):
            action = "repay"
        else:
            action = "hold"

    return {
        "action": action,
        "invest_amount": float(invest_amount),
        "invest_mode": invest_mode,
        "ticker": ticker,
        "signal": inv["signal"],
        "signal_confidence": int(inv["confidence"]),
        "suggested_sip": float(inv.get("sip_suggested_amount", 0.0)),
    }
