import asyncio

import pandas as pd

from pocketoptionapi.stable_api import PocketOption


class PocketOptionBot:
    async def connect(self, ssid: str) -> None:
        self.ssid = ssid
        self.api = PocketOption(ssid)
        self.api.connect()
        while not self.api.check_connect():
            await asyncio.sleep(1)

    async def fetch_candles(
        self, symbol: str, timeframe: int, candles_to_check: int
    ) -> pd.DataFrame:
        counter = 0
        data = None
        while data is None:
            data = await self.api.get_candles(
                symbol, timeframe, None, timeframe * candles_to_check
            )
            counter += 1
            if counter == 3:
                raise FetchingCandlesMultipleAttemptsException("Error fetching candles")
        return data

    async def execute_order(
        self, amount: int, symbol: str, action: str, expiration_seconds: int
    ) -> None:
        result = False
        counter = 0
        while not result:
            result, _ = await self.api.buy(amount, symbol, action, expiration_seconds)
            counter += 1
            if counter == 10:
                raise ExecutingOrderMultipleAttemptsException("Error executing orders")


class BasePocketOptionBotException(Exception):
    """Base Exception class for PocketOptionBot Exceptions"""


class FetchingCandlesMultipleAttemptsException(BasePocketOptionBotException):
    """Exception while fetching candles after multiple attempts"""


class ExecutingOrderMultipleAttemptsException(BasePocketOptionBotException):
    """Exception while executing order after multiple attempts"""
