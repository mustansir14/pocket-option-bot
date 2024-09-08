from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd


class ITradingStrategy(ABC):
    @abstractmethod
    def get_next_action(self, data: pd.DataFrame) -> str:
        pass


class TradingStrategyEnum(str, Enum):
    LAST_X_CANDLES = "LAST_X_CANDLES"
    MOVING_AVERAGE = "MOVING_AVERAGE"
