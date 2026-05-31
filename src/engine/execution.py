import ccxt
import logging

class ExecutionEngine:
    def __init__(self, exchange: ccxt.bybit):
        self.ex = exchange
        self.ex.load_markets() # Pre-load to save latency during execution

    def get_active_positions(self) -> list:
        try:
            positions = self.ex.fetch_positions()
            return [p for p in positions if float(p['contracts']) > 0]
        except Exception as e:
            logging.error(f"Failed to fetch positions: {e}")
            return []

    def close_position(self, symbol: str, amount: float):
        try:
            return self.ex.create_market_sell_order(symbol, amount, params={'reduceOnly': True})
        except Exception as e:
            logging.error(f"Failed to close {symbol}: {e}")

    def execute_trade(self, symbol: str, current_price: float, amount_usdt: float, sl_pct: float):
        try:
            qty = float(self.ex.amount_to_precision(symbol, amount_usdt / current_price))
            sl = float(self.ex.price_to_precision(symbol, current_price * (1 - sl_pct)))

            if qty < self.ex.market(symbol)['limits']['amount']['min']:
                return None

            order = self.ex.create_order(
                symbol=symbol,
                type='market',
                side='buy',
                amount=qty,
                params={
                    'stopLoss': sl,
                    'slTriggerBy': 'LastPrice' # REQUIRED for Bybit V5 Linear
                }
            )
            return order
        except Exception as e:
            logging.error(f"Execution failed for {symbol}: {e}")
            return None
