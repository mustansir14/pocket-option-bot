import pandas as pd

from internal.trading_strategies import ITradingStrategy


class LastXCandlesTradingStrategy(ITradingStrategy):
    def get_next_action(self, data: pd.DataFrame) -> str:
        if all(data["close"] < data["open"]):
            return "call"
        if all(data["close"] > data["open"]):
            return "put"
        return ""
