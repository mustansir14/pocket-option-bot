from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List

import pandas as pd


class IBot(ABC):
    @abstractmethod
    async def connect(self, connection_info: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def fetch_candles(self, symbol: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        pass

    @abstractmethod
    def get_payout_for_symbol(self, symbol: str) -> int:
        pass


class BotEnum(str, Enum):
    POCKET_OPTION = "POCKET_OPTION"
    IQ_OPTION = "IQ_OPTION"


class BaseBotException(Exception):
    pass


class InvalidConnectionInfoException(BaseBotException):
    pass


class BotNotConnectedException(BaseBotException):
    pass


class PayoutNotFoundException(BaseBotException):
    pass