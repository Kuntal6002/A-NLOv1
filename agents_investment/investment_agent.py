# agents_investment/investment_agent.py
from __future__ import annotations
from typing import Dict, Any

from .market_generator import get_price, get_history
from .trading_bot import analyze_market, predict_price


risk_config: Dict[str, Dict[str, float]] = {
    "conservative": {
        "max_vol": 0.02,
        "max_alloc": 0.03,
        "lumpsum_factor": 0.0,
        "sip_factor": 0.7,
    },
    "balanced": {
        "max_vol": 0.03,
        "max_alloc": 0.06,
        "lumpsum_factor": 1.0,
        "sip_factor": 1.0,
    },
    "aggressive": {
        "max_vol": 0.05,
        "max_alloc": 0.12,
        "lumpsum_factor": 2.0,
        "sip_factor": 1.5,
    },
}


class Portfolio:
    """
    Simple holdings portfolio.

    cash: realized cash from sells (bank balance is managed separately
          in backend.utils via SIM_STATE).
    positions: ticker -> units.
    """

    def __init__(self, cash: float = 0.0):
        self.cash = float(cash)
        self.positions: Dict[str, float] = {}

    def buy(self, ticker: str, amount: float) -> Dict[str, Any]:
        amount = max(0.0, float(amount))
        if amount <= 0.0:
            return {"status": "noop", "ticker": ticker, "amount": 0.0, "units": 0.0}

        price = get_price(ticker)
        if price <= 0.0:
            return {"status": "failed", "ticker": ticker, "amount": 0.0, "units": 0.0}

        units = amount / price
        self.positions[ticker] = self.positions.get(ticker, 0.0) + units

        return {
            "status": "filled",
            "ticker": ticker,
            "amount": float(amount),
            "units": float(units),
            "price": float(price),
        }

    def sell(self, ticker: str, amount: float) -> Dict[str, Any]:
        amount = max(0.0, float(amount))
        if amount <= 0.0:
            return {"status": "noop", "ticker": ticker, "amount": 0.0, "units": 0.0}

        price = get_price(ticker)
        units_owned = self.positions.get(ticker, 0.0)
        if units_owned <= 0.0 or price <= 0.0:
            return {"status": "failed", "ticker": ticker, "amount": 0.0, "units": 0.0}

        max_cash = units_owned * price
        sell_cash = min(amount, max_cash)
        units = sell_cash / price

        self.positions[ticker] = max(0.0, units_owned - units)
        if self.positions[ticker] == 0.0:
            self.positions.pop(ticker, None)

        self.cash += sell_cash

        return {
            "status": "filled",
            "ticker": ticker,
            "amount": float(sell_cash),
            "units": float(units),
            "price": float(price),
        }

    def portfolio_value(self) -> float:
        total = self.cash
        for t, units in self.positions.items():
            p = get_price(t)
            total += units * p
        return float(total)


_global_portfolio = Portfolio(cash=0.0)


def get_positions() -> Dict[str, float]:
    return dict(_global_portfolio.positions)


def get_portfolio_value() -> float:
    return _global_portfolio.portfolio_value()


def buy(ticker: str, amount: float) -> Dict[str, Any]:
    return _global_portfolio.buy(ticker, amount)


def sell(ticker: str, amount: float) -> Dict[str, Any]:
    return _global_portfolio.sell(ticker, amount)


# ---------------- SIP + opportunity logic ---------------- #


def _compute_sip(state: Dict[str, Any], history: list[float], profile: str) -> float:
    cfg = risk_config.get(profile, risk_config["balanced"])

    cash = float(state.get("bank_balance", state.get("balance", 0.0)))
    income = float(state.get("monthly_income", state.get("income_rate", 0.0)))
    expense = float(state.get("monthly_expense", state.get("expense_rate", 0.0)))
    emergency_buffer = float(
        state.get("emergency_buffer", expense * 3.0 if expense > 0 else 0.0)
    )
    vol = float(state.get("volatility", 0.0))

    # Base SIP per spec
    base_sip = max(0.03 * income, 0.02 * cash)
    # Do not breach emergency buffer
    available = max(0.0, cash - emergency_buffer)
    sip = min(base_sip, available)

    # Adjust for risk profile + volatility
    sip *= cfg["sip_factor"]
    if vol > cfg["max_vol"]:
        sip *= 0.5  # dampen during high vol

    return max(0.0, float(sip))


def evaluate_investment_opportunity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified decision: combines trading signal, volatility, SIP logic, and risk profile.
    Returns both execution plan and suggested SIP.
    """
    ticker = "INDEX"
    history = get_history(ticker)
    signal_info = analyze_market(history)
    signal = signal_info["signal"]
    confidence = int(signal_info["confidence"])
    vol = float(signal_info["volatility"])
    profile = state.get("risk_profile", "balanced")
    cfg = risk_config.get(profile, risk_config["balanced"])

    pred_price = predict_price(history)
    last_price = history[-1] if history else pred_price
    trend_positive = pred_price > last_price

    sip_amount = _compute_sip(state, history, profile)

    mode = "sip"
    amount = sip_amount
    should_invest = sip_amount > 0.0 and vol <= cfg["max_vol"]

    # Lump‑sum only on strong BUY with positive trend and low vol
    if (
        signal == "buy"
        and confidence >= 75
        and trend_positive
        and vol < cfg["max_vol"]
        and cfg["lumpsum_factor"] > 0.0
    ):
        mode = "lumpsum"
        amount = sip_amount * cfg["lumpsum_factor"]
        should_invest = amount > 0.0

    return {
        "should_invest": bool(should_invest),
        "amount": float(max(amount, 0.0) if should_invest else 0.0),
        "mode": mode if should_invest else "sip",
        "signal": signal,
        "confidence": confidence,
        "ticker": ticker,
        "sip_suggested_amount": float(sip_amount),
    }
