import json
import os
import threading
from datetime import datetime, timedelta

class ProgressiveRiskManager:
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.lock = threading.Lock()
        self.PAUSE_L1, self.PAUSE_L2, self.PAUSE_L3 = 7, 120, 720
        self.L3_THRESHOLD = -0.05
        self.state = self.load_state()
    def set_running_status(self, is_running: bool):
        """Global toggle for signal processing logic."""
        with self.lock:
            self.state['is_running'] = is_running
            self.save_state()

    def get_statistics(self) -> str:
        """Aggregates historical trade data for performance reporting."""
        with self.lock:
            trades = self.state.get('trade_history', [])
        
        if not trades: 
            return "📊 <b>Performance data unavailable:</b> No closed trades found."
        
        # Calculate key performance indicators (KPIs)
        rets = [t['ret'] for t in trades]
        total_pnl = (np.prod([1 + r for r in rets]) - 1) * 100
        winrate = (len([r for r in rets if r > 0]) / len(rets)) * 100
        
        gross_profit = sum([r for r in rets if r > 0])
        gross_loss = abs(sum([r for r in rets if r < 0]))
        pf = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
        return (f"📈 <b>Strategy Performance:</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💰 Compounded PnL: <b>{total_pnl:.2f}%</b>\n"
                f"⚖️ Profit Factor: <b>{pf:.2f}</b>\n"
                f"🎯 Current Winrate: <b>{winrate:.1f}%</b>\n"
                f"🔢 Sample Size: <b>{len(rets)} trades</b>")
    def load_state(self) -> dict:
        with self.lock:
            if os.path.exists(self.state_file):
                try:
                    with open(self.state_file, 'r') as f:
                        s = json.load(f)
                        if s.get('paused_until'):
                            s['paused_until'] = datetime.fromisoformat(s['paused_until'])
                        return s
                except json.JSONDecodeError:
                    pass
            return {'paused_until': None, 'trade_history': [], 'active_symbols': [], 'is_running': True}

    def save_state(self):
        with self.lock:
            s_copy = self.state.copy()
            if s_copy['paused_until']:
                s_copy['paused_until'] = s_copy['paused_until'].isoformat()
            with open(self.state_file, 'w') as f:
                json.dump(s_copy, f, indent=4)

    def is_on_cooldown(self) -> bool:
        if self.state['paused_until'] and datetime.utcnow() >= self.state['paused_until']:
            self.state['paused_until'] = None
            self.save_state()
        return self.state['paused_until'] is not None

    def register_trade(self, symbol: str, pnl: float, is_stop_loss: bool):
        """Registers a completed trade and escalates circuit breakers if needed."""
        now = datetime.utcnow()
        trade_record = {'time': now.isoformat(), 'is_sl': is_stop_loss, 'ret': pnl, 'sym': symbol}
        
        self.state['trade_history'].append(trade_record)
        
        if is_stop_loss:
            pause = self.PAUSE_L1
            th = self.state['trade_history']
            
            if len(th) >= 2 and th[-1]['is_sl'] and th[-2]['is_sl']:
                pause = self.PAUSE_L2
                
            if len(th) >= 3:
                last_3 = th[-3:]
                if sum(1 for x in last_3 if x['is_sl']) >= 2 and sum(x['ret'] for x in last_3) <= self.L3_THRESHOLD:
                    pause = self.PAUSE_L3
            
            self.state['paused_until'] = now + timedelta(hours=pause)
        
        self.save_state()
