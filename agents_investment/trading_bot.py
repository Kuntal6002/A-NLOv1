# backend/agents_investment/trading_bot.py
from typing import Dict, List
import math


def _sma(values: List[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / float(window)


def _volatility(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    rets = []
    for i in range(1, len(values)):
        if values[i - 1] > 0:
            rets.append((values[i] - values[i - 1]) / values[i - 1])
    if not rets:
        return 0.0
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / len(rets)
    return math.sqrt(var)


def analyze_market(history: List[float]) -> Dict[str, any]:
    if not history:
        return {"signal": "hold", "confidence": 0, "volatility": 0.0}
    short = _sma(history, 5) or history[-1]
    long = _sma(history, 20) or short
    price = history[-1]
    vol = _volatility(history)

    signal = "hold"
    conf = 10

    # moving average crossover + breakout
    if short > long * 1.01 and price > long:
        signal = "buy"
        conf = 70
        if vol < 0.02:
            conf += 20
    elif short < long * 0.99 and price < long:
        signal = "sell"
        conf = 70
        if vol > 0.03:
            conf += 20

    # volatility filter
    if vol > 0.06:
        signal = "hold"
        conf = 20

    return {
        "signal": signal,
        "confidence": min(100, max(0, int(conf))),
        "volatility": vol,
    }


def predict_price(history: List[float]) -> float:
    if not history:
        return 0.0
    if len(history) < 3:
        return float(history[-1])
    # linear trend on last N points
    n = min(10, len(history))
    ys = history[-n:]
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n)) or 1.0
    slope = num / den
    intercept = mean_y - slope * mean_x
    next_x = n
    pred = intercept + slope * next_x
    return float(max(0.0, pred))
