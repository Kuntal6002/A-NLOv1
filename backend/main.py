# backend/main.py
from typing import Any, Dict, List
import os
import sys
from dotenv import load_dotenv

# Ensure project root is on path so `agents` and `agents_core` packages can be found
# Adjust the path calculation if your project layout differs.
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio  # stdlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# local package imports (these rely on sys.path above)
from . import database as db
from . import models  # still used for other endpoints if you want
from . import utils
from agents_core.cycle import run_cycle

# Import Alpaca modules (these live in top-level `agents` package)
from agents.alpaca_mcp import AlpacaMCP
from agents.llm_trader import LLMTrader

# ============================================================
# AUTONOMOUS AGENT CYCLE RUNNER (Automatic AI Loop)
# ============================================================
AUTO_CYCLE_INTERVAL = 10  # seconds (edit for hackathon demo)

async def auto_cycle_runner():
    """
    Runs the AI cycle automatically every N seconds.
    Non-blocking, safe, continues until app shutdown.
    """
    # small delay so server boots cleanly
    await asyncio.sleep(2)
    print("🔥 Auto Agent Cycle Started...")

    while True:
        try:
            # run_cycle may be synchronous — run it off the event loop to avoid blocking.
            output = await asyncio.to_thread(run_cycle)

            # store output (utils.store_run_cycle_output may be sync)
            utils.store_run_cycle_output(
                output.get("state") or {},
                output.get("plan") or {},
                output.get("result") or {},
                float(output.get("reward") or 0.0),
                output.get("timestamp") or "",
            )

            print("✔ Auto cycle executed.")
        except Exception as e:
            # don't raise — log and continue
            print(f"❌ Auto cycle error: {type(e).__name__}: {e}")

        await asyncio.sleep(AUTO_CYCLE_INTERVAL)


app = FastAPI(title="A-NLO Backend")

@app.on_event("startup")
async def startup_event():
    # Initialize DB and any other start-up tasks here (so import time is clean)
    try:
        db.init_db()
        print("✅ Database initialized.")
    except Exception as e:
        print(f"⚠️ Database init error: {e}")

    # Initialize Alpaca components (require env variables; safe to init here)
    # Note: keep these global if you want them accessible in endpoints.
    global alpaca_mcp, llm_trader
    alpaca_api_key = os.getenv("ALPACA_API_KEY", "your_paper_api_key")
    alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY", "your_paper_secret_key")
    alpaca_mcp = AlpacaMCP(alpaca_api_key, alpaca_secret_key, paper=True)
    llm_trader = LLMTrader(alpaca_mcp)

    # Start background auto-cycle runner
    asyncio.create_task(auto_cycle_runner())
    print("🚀 Agentic Auto-cycle initialized...")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request validation
class CommandRequest(BaseModel):
    command: str

class TradeRequest(BaseModel):
    symbol: str
    qty: float
    side: str  # "buy" or "sell"

# ============================================================
# EXISTING ENDPOINTS
# ============================================================

@app.get("/state")
def get_state_endpoint() -> Dict[str, Any]:
    return utils.get_state()

@app.get("/portfolio")
def get_portfolio_endpoint() -> Dict[str, Any]:
    return utils.get_portfolio()

@app.get("/transactions")
def get_transactions_endpoint() -> List[Dict[str, Any]]:
    return utils.get_transactions()

@app.post("/transactions")
def create_transaction_endpoint(tx: Dict[str, Any]) -> Dict[str, Any]:
    utils.insert_transaction(tx)
    rows = utils.get_transactions()
    # return last inserted or fallback constructed object
    return rows[-1] if rows else {
        "id": 1,
        "timestamp": tx.get("date", ""),
        "type": tx.get("type", "manual"),
        "category": tx.get("category", ""),
        "amount": float(tx.get("amount", 0.0)),
        "description": tx.get("description", ""),
        "balance_after": utils.SIM_STATE.get("bank_balance") if hasattr(utils, "SIM_STATE") else None,
    }

@app.get("/market")
def get_market_endpoint() -> Dict[str, Any]:
    return utils.get_market()

@app.get("/logs")
def get_logs_endpoint() -> List[Dict[str, Any]]:
    return utils.get_logs()

@app.post("/run_cycle")
def run_cycle_endpoint() -> Dict[str, Any]:
    # run_cycle is potentially CPU-bound / sync — run in thread to avoid blocking uvicorn workers
    output = asyncio.get_event_loop().run_until_complete(asyncio.to_thread(run_cycle))
    cycle_id = utils.store_run_cycle_output(
        output.get("state") or {},
        output.get("plan") or {},
        output.get("result") or {},
        float(output.get("reward") or 0.0),
        output.get("timestamp") or "",
    )
    output["cycle"] = cycle_id
    return output

@app.post("/reset")
def reset_endpoint() -> Dict[str, str]:
    db.reset_db()
    utils.reset_sim_state()
    return {"status": "ok"}

# ============================================================
# NEW ALPACA PAPER TRADING ENDPOINTS
# ============================================================

@app.post("/alpaca/command")
async def execute_command(request: CommandRequest) -> Dict[str, Any]:
    """
    Execute a natural language trading command via LLM + MCP
    Example: {"command": "Buy 10 AAPL"}
    """
    try:
        # LLMTrader.process_command may be synchronous — run in thread if blocking
        result = await asyncio.to_thread(llm_trader.process_command, request.command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alpaca/buy")
async def place_buy_order(request: TradeRequest) -> Dict[str, Any]:
    try:
        result = await asyncio.to_thread(alpaca_mcp.buy, request.symbol, request.qty)
        if result.get("success"):
            return {"status": "success", "order": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Buy order failed"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alpaca/sell")
async def place_sell_order(request: TradeRequest) -> Dict[str, Any]:
    try:
        result = await asyncio.to_thread(alpaca_mcp.sell, request.symbol, request.qty)
        if result.get("success"):
            return {"status": "success", "order": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Sell order failed"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alpaca/account")
async def get_account() -> Dict[str, Any]:
    try:
        account = await asyncio.to_thread(alpaca_mcp.get_account)
        if account.get("success"):
            return account
        else:
            raise HTTPException(status_code=500, detail=account.get("error", "Failed to get account"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alpaca/positions")
async def get_positions() -> Dict[str, Any]:
    try:
        positions = await asyncio.to_thread(alpaca_mcp.get_all_positions)
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alpaca/position/{symbol}")
async def get_position(symbol: str) -> Dict[str, Any]:
    try:
        position = await asyncio.to_thread(alpaca_mcp.get_position, symbol.upper())
        if position.get("success"):
            return position
        else:
            raise HTTPException(status_code=404, detail=f"No position found for {symbol}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alpaca/status")
async def get_alpaca_status() -> Dict[str, Any]:
    try:
        account = await asyncio.to_thread(alpaca_mcp.get_account)
        positions = await asyncio.to_thread(alpaca_mcp.get_all_positions)

        total_unrealized_pl = 0.0
        for p in positions:
            try:
                total_unrealized_pl += float(p.get("unrealized_pl", 0))
            except Exception:
                pass

        return {
            "account": account if account.get("success") else {},
            "positions": positions,
            "position_count": len(positions),
            "total_unrealized_pl": total_unrealized_pl,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
