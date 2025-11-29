# agents_investment/market_generator.py
import math
import random
from typing import Dict, List, Tuple

# Simple GBM-based market state
_state: Dict[str, Dict[str, float | List[float]]] = {
    # Daily drift ~0.08% (≈ 20% annual), vol ~2% daily (visibly moves)
    "INDEX": {"price": 100.0, "history": [], "mu": 0.0008, "sigma": 0.02},
    "STOCK_A": {"price": 60.0, "history": [], "mu": 0.0010, "sigma": 0.03},
    "STOCK_B": {"price": 140.0, "history": [], "mu": 0.0004, "sigma": 0.025},
}


def set_index_volatility(sigma: float) -> None:
    """
    Clamp INDEX daily volatility to [0.005, 0.05].
    """
    sigma = max(0.005, min(0.05, float(sigma)))
    _state["INDEX"]["sigma"] = sigma  # type: ignore[assignment]


def _step_gbm(ticker: str) -> None:
    """
    One GBM step: S_{t+1} = S_t * exp((mu - 0.5*sigma^2) + sigma * Z),
    with Z ~ N(0, 1). [web:100]
    """
    d = _state[ticker]
    price = float(d["price"])          # type: ignore[arg-type]
    mu = float(d["mu"])               # type: ignore[arg-type]
    sigma = float(d["sigma"])         # type: ignore[arg-type]

    z = random.gauss(0.0, 1.0)
    log_ret = (mu - 0.5 * sigma ** 2) + sigma * z
    new_price = price * math.exp(log_ret)

    # Ensure strictly positive and never exactly flat
    if new_price <= 0.0 or abs(new_price - price) < 1e-6:
        direction = 1.0 if z >= 0 else -1.0
        new_price = price * (1.0 + 0.003 * direction)

    d["price"] = new_price
    history: List[float] = d["history"]  # type: ignore[assignment]
    history.append(new_price)
    if len(history) > 2000:
        history.pop(0)


def step_market() -> None:
    """
    Advance the market by one simulated day.
    Called once per agent cycle.
    """
    for t in _state.keys():
        _step_gbm(t)


def get_price(ticker: str) -> float:
    if ticker not in _state:
        ticker = "INDEX"
    # Do NOT advance here; stepping is controlled by step_market()
    return float(_state[ticker]["price"])  # type: ignore[return-value]


def get_history(ticker: str) -> List[float]:
    if ticker not in _state:
        ticker = "INDEX"
    return list(_state[ticker]["history"])  # copy so callers can't mutate


def _ensure_bootstrap() -> None:
    """
    Guarantee at least 200 historical points so charts are never flat.
    """
    if not _state["INDEX"]["history"]:
        for _ in range(200):
            step_market()


def _realized_volatility(prices: List[float]) -> float:
    if len(prices) < 2:
        return 0.0
    rets = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            rets.append((prices[i] - prices[i - 1]) / prices[i - 1])
    if not rets:
        return 0.0
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / len(rets)
    return math.sqrt(var)


def get_index_metrics() -> Tuple[List[float], float, float, float]:
    """
    Returns (price_history, current_price, volatility, total_return)
    for INDEX.
    """
    _ensure_bootstrap()
    hist = get_history("INDEX")
    current = hist[-1] if hist else 100.0
    vol = _realized_volatility(hist)
    if len(hist) >= 2 and hist[0] > 0:
        total_ret = hist[-1] / hist[0] - 1.0
    else:
        total_ret = 0.0
    return hist, float(current), float(vol), float(total_ret)


# Seed history on import
_ensure_bootstrap()
