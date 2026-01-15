from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any

import pandas as pd


class IBot(ABC):
    @abstractmethod
    async def connect(self, connection_info: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def fetch_candles(self, symbol: str) -> pd.DataFrame:
        pass


class BotEnum(str, Enum):
    POCKET_OPTION = "POCKET_OPTION"
    IQ_OPTION = "IQ_OPTION"


class BaseBotException(Exception):
    pass


class InvalidConnectionInfoException(BaseBotException):
    pass
