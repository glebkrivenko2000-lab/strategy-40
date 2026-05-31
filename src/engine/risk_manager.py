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
