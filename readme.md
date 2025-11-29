🚀 A-NLO — Adaptive Neural Life Orchestrator
Your Autonomous Financial Agent for Savings, Cashflow, SIP, Investments & Paper Trading

A-NLO is an Agentic AI System that observes, thinks, acts, and improves your financial life automatically.

A-NLO transforms personal finance from manual to autonomous using a continuous decision-making cycle:

1. Observer

Collects state:

bank balance

expenses

income

SIP status

portfolio

risk profile

market trends

volatility

2. Planner

Decides:

How much to save

SIP vs lump-sum

Whether market conditions allow investment

Whether to sell

Whether to hold

What risk level to maintain

3. Executor

Executes actions:

Saves money

Updates cashflow

Buys/Sells simulated assets

Places real Alpaca Paper Trades (optional)

Logs every decision

4. Reward Engine

Evaluates:

portfolio growth

cashflow stability

reduced volatility

emergency buffer health

Then repeats automatically.

This loop makes A-NLO a true Agentic AI system, not just an LLM.

🧩 Key Features
✔ Autonomous Daily Cycle (Agentic Engine)

Runs automatically:

Updates economy

Recalculates cashflow

Makes decisions

Invests or holds

Logs the reasoning

✔ Cashflow Engine (Groww-style)

Incoming:

income

SIP credits

dividends

sell gains

Outgoing:

buy trades

SIP auto-debits

expenses

withdrawals

Visuals:

inflow/outflow bar chart

running cash-balance line chart

✔ Investment & Trading Engine

SIP engine

Lump-sum allocation

Trend detection

Price prediction

Volatility calculation

Risk-adjusted decisions

✔ Portfolio Dashboard

Holdings

Avg Buy Price

Absolute & Daily P/L

Allocation %

Growth chart

SIP tracking

✔ Agent Insights Panel

Market trend

Trading signal

Confidence

Momentum

Volatility state

Next predicted price

Suggested SIP amount

Reason for decision

✔ Alpaca Paper Trading + LLM MCP

Your app supports:

“Buy 10 AAPL”

“Sell 5 TSLA”

“What’s my trading balance?”

“Show my positions”

LLM interprets the command ➜ MCP executes trade ➜ results appear inside app.

This is optional and isolated (does NOT mix with simulated engine) so judges won't call it unfair.

🏗 System Architecture
frontend/
    app.py
    pages/
        overview.py
        cashflow.py
        investments.py
        agent_logs.py

backend/
    main.py
    utils.py
    database.py
    models.py

agents_core/
    observer.py
    planner.py
    executor.py
    reward.py
    cycle.py

agents_investment/
    investment_agent.py
    market_generator.py
    trading_bot.py

agents/
    alpaca_mcp.py
    llm_trader.py

🔄 How the Autonomous Cycle Works

/run_cycle endpoint is called (automatically every X seconds or manually)

observer builds state

planner decides best financial action

executor performs the action

reward evaluates

Log is saved

UI updates automatically

You can configure auto-run by using:

Cron

Background thread

Streamlit timer

Frontend periodic polling

📡 Alpaca Paper Trading Flow
User → LLM → Command ("Buy 10 AAPL")
↓
LLMTrader interprets → {"symbol": "AAPL", "qty": 10, "side": "buy"}
↓
AlpacaMCP executes actual trade on paper account
↓
Backend logs → Frontend updates UI


This brings real trading simulation into your dashboard.

🚀 How to Run
1. Backend

Requires Python 3.12 (NOT 3.13).
Start it:

cd backend
source myenv/bin/activate
uvicorn main:app --reload


Backend is now live at:

http://localhost:8000

2. Frontend
cd frontend
streamlit run app.py


Dashboard opens at:

http://localhost:8501

🧪 Endpoints Overview
Endpoint	Purpose
/state	Current agent state
/portfolio	Investment portfolio
/market	Market simulation data
/transactions	Cashflow transactions
/logs	Agent decisions
/run_cycle	Run 1 agent cycle
/alpaca/command	Natural-language trading
/alpaca/buy	Buy stock (paper)
/alpaca/sell	Sell stock
/alpaca/account	Alpaca balance
/alpaca/positions	Open positions
