"""AI-Powered Trading Agent with Groq LLM"""
import os
import re
import json
from typing import Dict, Any
from pathlib import Path

# Load .env BEFORE Groq import
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
except Exception as e:
    print(f"⚠️ Could not load .env: {e}")

from groq import Groq

class LLMTrader:
    def __init__(self, alpaca_mcp):
        self.mcp = alpaca_mcp

        # Get Groq API key with validation
        groq_key = os.getenv('GROQ_API_KEY')

        if not groq_key:
            print("⚠️ WARNING: GROQ_API_KEY not found! AI features disabled, using regex fallback.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=groq_key)
                print(f"✅ Groq AI initialized: {groq_key[:10]}...")
            except Exception as e:
                print(f"❌ Groq initialization failed: {e}")
                self.client = None

    def process_command(self, command: str) -> Dict[str, Any]:
        """Process natural language → trading action"""

        # If no AI client, use regex fallback
        if not self.client:
            return self._process_with_regex(command)

        # Get account context for AI
        try:
            account = self.mcp.get_account()
            positions = self.mcp.get_all_positions()
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to get account data: {str(e)}"
            }

        # AI Prompt
        prompt = f"""You are a trading assistant. Analyze this command and execute it.

Account: Equity ${account.get('equity', 0)}, Cash ${account.get('cash', 0)}
Positions: {len(positions)} open positions

User command: "{command}"

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
    "action": "buy",
    "symbol": "AAPL",
    "quantity": 10,
    "reasoning": "Buying because..."
}}

Valid actions: buy, sell, status, hold
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )

            ai_response = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            ai_response = re.sub(r'``````', '', ai_response)

            # Parse AI JSON
            try:
                decision = json.loads(ai_response)
            except json.JSONDecodeError:
                print(f"⚠️ AI returned invalid JSON: {ai_response[:100]}")
                decision = self._regex_fallback(command)

            return self._execute_decision(decision)

        except Exception as e:
            print(f"❌ AI error: {str(e)}, using regex fallback")
            return self._process_with_regex(command)

    def _process_with_regex(self, command: str) -> Dict[str, Any]:
        """Process command with regex fallback"""
        decision = self._regex_fallback(command)
        return self._execute_decision(decision)

    def _regex_fallback(self, command: str) -> Dict[str, Any]:
        """Parse command using regex patterns"""
        cmd_lower = command.lower()

        # Buy pattern: "buy 10 AAPL"
        buy_match = re.search(r'buy\s+(\d+(?:\.\d+)?)\s+([a-z]+)', cmd_lower)
        if buy_match:
            qty, symbol = buy_match.groups()
            return {
                "action": "buy",
                "symbol": symbol.upper(),
                "quantity": float(qty),
                "reasoning": "Regex parsed buy command"
            }

        # Sell pattern: "sell 5 TSLA"
        sell_match = re.search(r'sell\s+(\d+(?:\.\d+)?)\s+([a-z]+)', cmd_lower)
        if sell_match:
            qty, symbol = sell_match.groups()
            return {
                "action": "sell",
                "symbol": symbol.upper(),
                "quantity": float(qty),
                "reasoning": "Regex parsed sell command"
            }

        # Default to status
        return {
            "action": "status",
            "reasoning": "Command not recognized, showing status"
        }

    def _execute_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trading decision"""
        action = decision.get("action", "hold")

        if action == "buy":
            symbol = decision.get("symbol", "UNKNOWN")
            qty = decision.get("quantity", 0)

            try:
                result = self.mcp.buy(symbol, qty)
                return {
                    'success': result.get('success', False),
                    'message': f"✅ Bought {qty} {symbol}" if result.get('success') else f"❌ Buy failed: {result.get('error')}",
                    'order_details': result,
                    'ai_reasoning': decision.get('reasoning', 'Trade executed'),
                    'action': 'buy'
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f"❌ Buy error: {str(e)}",
                    'ai_reasoning': decision.get('reasoning', '')
                }

        elif action == "sell":
            symbol = decision.get("symbol", "UNKNOWN")
            qty = decision.get("quantity", 0)

            try:
                result = self.mcp.sell(symbol, qty)
                return {
                    'success': result.get('success', False),
                    'message': f"✅ Sold {qty} {symbol}" if result.get('success') else f"❌ Sell failed: {result.get('error')}",
                    'order_details': result,
                    'ai_reasoning': decision.get('reasoning', 'Trade executed'),
                    'action': 'sell'
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f"❌ Sell error: {str(e)}",
                    'ai_reasoning': decision.get('reasoning', '')
                }

        elif action == "status":
            try:
                account = self.mcp.get_account()
                positions = self.mcp.get_all_positions()
                return {
                    'success': True,
                    'message': f"📊 Equity: ${account.get('equity', 0)}, Positions: {len(positions)}",
                    'account': account,
                    'positions': positions,
                    'ai_reasoning': decision.get('reasoning', 'Account status')
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f"❌ Status error: {str(e)}"
                }

        return {
            'success': False,
            'message': "🤔 No action taken",
            'ai_reasoning': decision.get('reasoning', 'No valid action')
        }
