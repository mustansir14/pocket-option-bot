import pandas as pd

from internal.trading_strategies import ITradingStrategy


class MovingAverageTradingStrategy(ITradingStrategy):
    def __init__(self, fast_period: int, slow_period: int):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def get_next_action(self, data: pd.DataFrame) -> str:
        # Calculate moving averages
        data["fast_ma"] = data["close"].rolling(window=self.fast_period).mean()
        data["slow_ma"] = data["close"].rolling(window=self.slow_period).mean()

        # Check for crossover
        if (
            data["fast_ma"].iloc[-2] < data["slow_ma"].iloc[-2]
            and data["fast_ma"].iloc[-1] > data["slow_ma"].iloc[-1]
        ):
            return "call"  # Fast MA crosses above Slow MA -> Buy signal
        if (
            data["fast_ma"].iloc[-2] > data["slow_ma"].iloc[-2]
            and data["fast_ma"].iloc[-1] < data["slow_ma"].iloc[-1]
        ):
            return "put"  # Fast MA crosses below Slow MA -> Sell signal
        return ""  # No action
