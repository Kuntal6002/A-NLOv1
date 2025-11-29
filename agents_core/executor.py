# agents_core/executor.py
from typing import Dict, Any

from backend import utils


def execute(plan: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    action = plan.get("action", "hold")
    amount = float(plan.get("invest_amount", 0.0))
    ticker = plan.get("ticker", "INDEX")
    mode = plan.get("invest_mode", "sip")
    timestamp = plan.get("timestamp", "")

    if action == "invest" and amount > 0.0:
        return utils.apply_investment(timestamp, mode, ticker, amount)
    elif action == "repay":
        # model as an extra expense transaction
        repay_amt = max(0.0, amount)
        utils.SIM_STATE["bank_balance"] -= repay_amt
        utils._log_transaction(
            timestamp, "repay", repay_amt, "debt repayment", "expense"
        )
        utils.SIM_STATE["balance_history"].append(utils.SIM_STATE["bank_balance"])
        return {"status": "repaid", "amount": float(repay_amt)}
    elif action == "save":
        return {"status": "saved"}
    else:
        return {"status": "hold"}
