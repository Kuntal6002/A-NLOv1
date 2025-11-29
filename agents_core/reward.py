# agents_core/reward.py
from typing import Dict, Any


def compute_reward(state: Dict[str, Any], result: Dict[str, Any]) -> float:
    """
    Reward is driven by profit on the amount invested this cycle,
    with small penalties for liquidity risk and excessive volatility.

    - If we invest X and NAV increases by ΔNAV, reward ≈ ΔNAV (rupee profit).
    - If we don't invest, NAV change still counts but with lower weight.
    """

    nav_hist = state.get("nav_history") or []
    invest_amt = float(state.get("last_invest_amount", 0.0))
    reward = 0.0

    # 1) Profit-based component: NAV change
    if len(nav_hist) >= 2:
        nav_prev = float(nav_hist[-2])
        nav_curr = float(nav_hist[-1])
        nav_change = nav_curr - nav_prev  # absolute profit/loss this cycle

        if invest_amt > 0.0:
            # Full credit when we actually invested this cycle
            reward += nav_change
        else:
            # Smaller weight if we were just holding
            reward += nav_change * 0.2

    # 2) Liquidity safety: penalize if emergency buffer is broken
    if not state.get("emergency_buffer_ok", True):
        reward -= 0.5

    # 3) Volatility penalty: discourage high-risk regimes
    vol = float(state.get("volatility", 0.0))
    if vol > 0.04:
        reward -= 0.2
    if vol > 0.07:
        reward -= 0.5

    # 4) Tiny bonus for taking an action that actually executed
    if result.get("status") in ("filled", "saved"):
        reward += 0.05

    return float(reward)
