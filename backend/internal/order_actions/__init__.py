from abc import ABC, abstractmethod
from enum import Enum


class IOrderAction(ABC):
    @abstractmethod
    async def execute(
        self, symbol: str, action: str, expiration_seconds: int, profit_rate: int
    ) -> None:
        pass


class OrderActionEnum(str, Enum):
    EXECUTE_ORDER = "EXECUTE_ORDER"
    TELEGRAM_SIGNAL = "TELEGRAM_SIGNAL"
