from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    Interface for all Alpha strategies.
    Decouples signal generation logic from execution engine.
    """
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process raw OHLCV into features/indicators."""
        pass

    @abstractmethod
    def check_entry_signal(self, symbol: str, df: pd.DataFrame, macro_condition: bool) -> dict:
        """
        Evaluate entry conditions.
        Returns: {'action': 'BUY'|'HOLD', 'price': float, 'sl': float}
        """
        pass

    @abstractmethod
    def check_exit_signal(self, symbol: str, df: pd.DataFrame, entry_price: float) -> bool:
        """Evaluate exit/trailing conditions."""
        pass
