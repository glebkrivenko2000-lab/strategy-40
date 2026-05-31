import time
import threading
from datetime import datetime
from config import Config
from engine.execution import ExecutionEngine
from engine.risk_manager import ProgressiveRiskManager
from strategy.momentum_alpha import MomentumAlpha
from utils.telegram_bot import TelegramUI

def main():
    # Dependency Injection
    import ccxt
    exchange = ccxt.bybit({'apiKey': Config.API_KEY, 'secret': Config.API_SECRET})
    exchange.set_sandbox_mode(Config.IS_TESTNET)
    
    engine = ExecutionEngine(exchange)
    risk_mgr = ProgressiveRiskManager(Config.STATE_FILE)
    alpha = MomentumAlpha(Config.LOOKBACK_HOURS, 72, Config.MIN_ER_THRESHOLD, Config.STOP_LOSS_PCT)
    ui = TelegramUI(Config.TG_TOKEN, Config.TG_CHAT_ID)

    # Launch UI Thread
    threading.Thread(target=ui.run, daemon=True).start()

    while True:
        now = datetime.utcnow()
        if now.minute == 0 and 5 <= now.second <= 15:
            if not risk_mgr.state['is_running'] or risk_mgr.is_on_cooldown():
                time.sleep(60)
                continue

            # 1. Macro Filter
            eth_data = engine.get_market_data('ETH/USDT:USDT', limit=210)
            eth_df = alpha.calculate_indicators(eth_data)
            macro_ok = eth_df['close'].iloc[-1] > eth_df['sma_exit'].iloc[-1]

            if macro_ok:
                # 2. Scanning for opportunities
                # [LOGIC]: Fetch tickers, sort by volume, check signal...
                pass 
            
            time.sleep(60)
        time.sleep(1)

if __name__ == "__main__":
    main()
