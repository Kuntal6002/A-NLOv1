🚀 A-NLO — Adaptive Neural Life Orchestrator
Your Autonomous Financial Agent for Savings, Cashflow, SIP, Investments & Paper Trading

A-NLO is an Agentic AI System that observes → thinks → acts → learns to improve your financial life automatically.

🌐 What A-NLO Does

A-NLO transforms personal finance from manual to autonomous, driven by a recurring decision-making loop:

🔁 The Autonomous Intelligence Cycle
1. 🛰 Observer

Collects real-time financial state:

Bank balance

Expenses & income

SIP status

Portfolio health

Risk profile

Market trend & momentum

Volatility conditions

2. 🧠 Planner

Decides the optimal move:

How much to save

SIP vs lump-sum

Whether market conditions allow investing

Whether to buy/sell/hold

Target risk level

Rebalancing needs

3. 🤖 Executor

Executes precise actions:

Saves money

Updates cashflow

Buys/Sells simulated assets

Places Alpaca Paper Trades (optional)

Logs every decision transparently

4. 🎯 Reward Engine

Evaluates progress:

Portfolio growth

Cashflow stability

Volatility reduction

Emergency buffer health

Then the system loops automatically, making A-NLO a true Agentic AI, not just another LLM app.

🧩 Key Features
✔ Autonomous Daily Cycle

A-NLO runs automatically:

Updates economy

Recalculates cashflow

Makes investment decisions

Executes trades

Logs reasoning

✔ Cashflow Engine (Groww-style)
Incoming:

Salary / income

SIP credits

Dividends

Sell gains

Outgoing:

Buy trades

SIP auto-debits

Expenses

Withdrawals

Visuals:

Inflow/Outflow bar chart

Running cash-balance line chart

✔ Investment & Trading Engine

SIP automation

Lump-sum allocation

Trend detection

Price prediction

Volatility calculation

Risk-adjusted decisions

✔ Portfolio Dashboard

Holdings

Average buy price

Absolute & daily P/L

Allocation %

Growth chart

SIP tracking

✔ Agent Insights Panel

Shows the AI’s thinking:

Market trend

Trading signal

Confidence

Momentum

Volatility state

Next predicted price

Suggested SIP amount

Reason for decision

✔ Alpaca Paper Trading + LLM MCP (Optional)

Supports natural-language commands like:

“Buy 10 AAPL”

“Sell 5 TSLA”

“What’s my trading balance?”

“Show my positions”

LLM → MCP → Execution → UI Update

This system is isolated from the simulated engine — so judges won’t consider it unfair.

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

/run_cycle is triggered (auto or manual)

Observer collects state

Planner selects best action

Executor performs the action

Reward Engine evaluates

Log is saved

UI updates live

Supports auto-run using:

Cron

Background thread

Streamlit timer

Frontend polling

📡 Alpaca Paper Trading Flow
User Command → LLM → Parsed Instruction
            ↓
   LLMTrader → {"symbol", "qty", "side"}
            ↓
        AlpacaMCP executes
            ↓
     Backend logs → UI refresh


This brings realistic trading simulation into your dashboard.

🚀 How to Run the Project
1. Backend Setup

Requires Python 3.12

cd backend
source myenv/bin/activate
uvicorn main:app --reload


Backend runs at: http://localhost:8000

2. Frontend
cd frontend
streamlit run app.py


Dashboard opens at: http://localhost:8501

🧪 API Endpoints Overview
Endpoint	Purpose
/state	Current agent state
/portfolio	Portfolio data
/market	Market simulation
/transactions	Cashflow transactions
/logs	Agent reasoning logs
/run_cycle	Run 1 autonomous cycle
/alpaca/command	Natural-language trading
/alpaca/buy	Buy stock (paper)
/alpaca/sell	Sell stock
/alpaca/account	Account info
/alpaca/positions	Open positions
