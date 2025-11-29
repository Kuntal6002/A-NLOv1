# agents/alpaca_mcp.py - FIXED FOR REAL TRADING
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
import os

class AlpacaMCP:
    def __init__(self, api_key, secret_key, paper=True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper

        # Trading client
        self.trading_client = TradingClient(
            api_key, secret_key, paper=paper
        )

        # Data client (quotes)
        self.data_client = StockHistoricalDataClient(
            api_key, secret_key
        )

    def get_account(self):
        """Get account info"""
        try:
            account = self.trading_client.get_account()
            return {
                'success': True,
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_all_positions(self):
        """Get all positions"""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    'symbol': pos.symbol,
                    'qty': float(pos.qty),
                    'market_value': float(pos.market_value),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'avg_entry_price': float(pos.avg_entry_price)
                }
                for pos in positions
            ]
        except Exception as e:
            return []

    def buy(self, symbol, qty):
        """Submit BUY order"""
        try:
            # Validate qty
            qty = float(qty)
            if qty <= 0:
                return {'success': False, 'error': 'Invalid quantity'}

            order_data = MarketOrderRequest(
                symbol=symbol.upper(),
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )

            order = self.trading_client.submit_order(order_data)

            return {
                'success': True,
                'order_id': str(order.id),
                'symbol': order.symbol,
                'qty': float(order.qty),
                'status': str(order.status),
                'submitted': str(order.submitted_at)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def sell(self, symbol, qty):
        """Submit SELL order"""
        try:
            qty = float(qty)
            if qty <= 0:
                return {'success': False, 'error': 'Invalid quantity'}

            order_data = MarketOrderRequest(
                symbol=symbol.upper(),
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )

            order = self.trading_client.submit_order(order_data)

            return {
                'success': True,
                'order_id': str(order.id),
                'symbol': order.symbol,
                'qty': float(order.qty),
                'status': str(order.status),
                'submitted': str(order.submitted_at)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
