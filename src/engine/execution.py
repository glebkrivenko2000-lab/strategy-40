import json
import os
import threading
from datetime import datetime, timedelta

class ProgressiveRiskManager:
    """
    Multi-tier Circuit Breaker system to prevent overtrading 
    and mitigate systemic risks during high-volatility regime shifts.
    """
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.lock = threading.Lock()
        self.PAUSE_L1 = 7
        self.PAUSE_L2 = 120
        self.PAUSE_L3 = 720
        self.L3_THRESHOLD = -0.05
        self.state = self._load_state()

    def load_state(self) -> dict:
        with self.lock:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    s = json.load(f)
                    if s['paused_until']:
                        s['paused_until'] = datetime.fromisoformat(s['paused_until'])
                    return s
            return {'paused_until': None, 'trade_history': [], 'active_symbols': [], 'is_running': True}

    def _save_state(self):
        # Internal save method - called within locks
        s_copy = self.state.copy()
        if s_copy['paused_until']:
            s_copy['paused_until'] = s_copy['paused_until'].isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(s_copy, f, indent=4)

    def is_on_cooldown(self) -> bool:
        if self.state['paused_until'] and datetime.utcnow() >= self.state['paused_until']:
            with self.lock:
                self.state['paused_until'] = None
                self._save_state()
        return self.state['paused_until'] is not None

    def register_stop_loss(self, symbol: str):
        """Activates progressive cooldown tiers (L1-L3)."""
        now = datetime.utcnow()
        with self.lock:
            self.state['trade_history'].append({'time': now.isoformat(), 'is_sl': True, 'ret': -0.05, 'sym': symbol})
            
            pause = self.PAUSE_L1
            th = self.state['trade_history']
            
            # Tier 2: Double consecutive SL
            if len(th) >= 2 and th[-1]['is_sl'] and th[-2]['is_sl']:
                pause = self.PAUSE_L2
            # Tier 3: Statistical Drawdown Limit
            if len(th) >= 3:
                last_3 = th[-3:]
                if sum(1 for x in last_3 if x['is_sl']) >= 2 and sum(x['ret'] for x in last_3) <= self.L3_THRESHOLD:
                    pause = self.PAUSE_L3
            
            self.state['paused_until'] = now + timedelta(hours=pause)
            self._save_state()
            return pause
