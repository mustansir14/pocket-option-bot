import asyncio
from typing import List

import pandas as pd

from internal.order_actions import IOrderAction
from pocketoptionapi_async.client import AsyncPocketOptionClient, Candle


class PocketOptionBot(IOrderAction):
    def __init__(self, order_amount: float = 1.0, timeframe: int = 30) -> None:
        self.order_amount = order_amount
        self.asset_payouts = {}
        self.timeframe = timeframe

    async def connect(self, ssid: str) -> None:
        self.ssid = ssid
        is_demo = '"isDemo":1' in ssid
        self.api = AsyncPocketOptionClient(ssid, is_demo=is_demo, enable_logging=False)
        while not await self.api.connect():
            await asyncio.sleep(1)

    async def fetch_candles(self, symbol: str, candles_to_check: int) -> pd.DataFrame:
        counter = 0
        data = None
        while data is None:
            data = await self.api.get_candles(symbol, self.timeframe, candles_to_check)
            counter += 1
            if counter == 3:
                raise FetchingCandlesMultipleAttemptsException("Error fetching candles")
        data = candles_to_dataframe(data)
        return data

    async def execute(
        self, symbol: str, action: str, expiration_seconds: int, profit_rate: int
    ) -> None:
        result = False
        counter = 0
        while not result:
            result, _ = await self.api.place_order(
                symbol, self.order_amount, action, expiration_seconds
            )
            counter += 1
            if counter == 10:
                raise ExecutingOrderMultipleAttemptsException("Error executing orders")


def candles_to_dataframe(candles: List[Candle]) -> pd.DataFrame:
    data = {
        "time": [candle.timestamp for candle in candles],
        "open": [candle.open for candle in candles],
        "close": [candle.close for candle in candles],
        "high": [candle.high for candle in candles],
        "low": [candle.low for candle in candles],
        "volume": [candle.volume for candle in candles],
    }
    return pd.DataFrame(data)


class BasePocketOptionBotException(Exception):
    """Base Exception class for PocketOptionBot Exceptions"""


class FetchingCandlesMultipleAttemptsException(BasePocketOptionBotException):
    """Exception while fetching candles after multiple attempts"""


class ExecutingOrderMultipleAttemptsException(BasePocketOptionBotException):
    """Exception while executing order after multiple attempts"""
