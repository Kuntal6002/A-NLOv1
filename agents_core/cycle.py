# agents_core/cycle.py
from typing import Dict, Any
import datetime as dt

from backend import utils
from agents_investment.market_generator import step_market
from .observer import observe
from .planner import plan
from .executor import execute
from .reward import compute_reward


def run_cycle() -> Dict[str, Any]:
    """
    One full agent cycle:
    - step market (GBM)
    - simulate unstable income & expenses
    - observe updated state
    - plan & execute investments
    - compute reward and update NAV history
    """
    timestamp = dt.datetime.utcnow().isoformat()

    # 1) Market price moves
    step_market()

    # 2) Income & expenses (unstable income model)
    cash_flows = utils.simulate_income_and_expense(timestamp)

    # 3) Observe current financial state
    state = observe()
    state.update(cash_flows)

    # 4) Planner chooses action
    plan_out = plan(state) or {}
    plan_out["timestamp"] = timestamp

    # 5) Executor applies action (invest / repay / save / hold)
    result = execute(plan_out, state) or {}

    # 6) Update NAV history and compute reward
    nav = utils.update_nav_history()
    state["nav"] = nav
    reward = compute_reward(state, result)

    return {
        "state": state,
        "plan": plan_out,
        "result": result,
        "reward": float(reward),
        "timestamp": timestamp,
    }
