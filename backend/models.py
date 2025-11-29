# backend/models.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TransactionIn(BaseModel):
    date: str
    type: str
    category: str
    amount: float
    description: Optional[str] = ""


class TransactionOut(BaseModel):
    id: int
    timestamp: str
    type: str
    category: str
    amount: float
    description: str
    balance_after: float | None = None


class StateResponse(BaseModel):
    balance: float
    income_rate: float
    expense_rate: float
    volatility: float
    portfolio_value: float
    emergency_buffer_ok: bool
    risk_profile: str
    bank_balance: float
    monthly_income: float
    monthly_expense: float
    emergency_buffer: float


class PortfolioResponse(BaseModel):
    cash: float
    positions: Dict[str, float]
    value: float


class MarketResponse(BaseModel):
    price_history: List[float]
    current_price: float
    volatility: float
    return_rate: float
    nav_history: List[float]
    sip_history: List[float]
    lumpsum_history: List[float]
    income_history: List[float]
    expense_history: List[float]
    balance_history: List[float]


class AgentLogOut(BaseModel):
    cycle: int
    timestamp: str
    state: Dict[str, Any]
    plan: Dict[str, Any]
    result: Dict[str, Any]
    reward: float


class RunCycleResponse(BaseModel):
    cycle: int
    state: Dict[str, Any]
    plan: Dict[str, Any]
    result: Dict[str, Any]
    reward: float
    timestamp: str


class ResetResponse(BaseModel):
    status: str
