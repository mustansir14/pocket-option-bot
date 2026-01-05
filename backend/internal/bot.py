import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import List

import pandas as pd

from internal.order_actions import IOrderAction
from pocketoptionapi_async.client import AsyncPocketOptionClient, Candle


@dataclass
class ActiveCandle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float


class PocketOptionBot(IOrderAction):
    def __init__(
        self, order_amount: float = 1.0, timeframe: int = 60, max_candles: int = 100
    ) -> None:
        self.order_amount = order_amount
        self.timeframe = timeframe
        self.max_candles = max_candles

        self._candles = defaultdict(
            lambda: pd.DataFrame(columns=["time", "open", "high", "low", "close"])
        )

        self._lock = asyncio.Lock()
        self._candles_fetched_lock = asyncio.Lock()
        self.candles_fetched = defaultdict(lambda: False)
        self._active = {}  # symbol -> ActiveCandle

    async def connect(
        self,
        ssid: str,
    ) -> None:
        self.ssid = ssid

        is_demo = '"isDemo":1' in ssid
        self.api = AsyncPocketOptionClient(ssid, is_demo=is_demo, enable_logging=False)
        while not await self.api.connect():
            await asyncio.sleep(1)
        self.api.add_event_callback("json_data", self.on_tick)

    def _get_candle_timestamp(self, ts: float) -> int:
        return int(ts // self.timeframe * self.timeframe)

    async def on_tick(self, data: list):
        if len(data) != 1:
            return
        if len(data[0]) != 3:
            return
        for symbol, ts, price in data:
            candle_ts = self._get_candle_timestamp(ts)

            async with self._lock:
                active = self._active.get(symbol)

                # First tick ever for symbol
                if active is None:
                    self._active[symbol] = ActiveCandle(
                        timestamp=candle_ts,
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                    )
                    continue

                # Same candle → update
                if active.timestamp == candle_ts:
                    active.high = max(active.high, price)
                    active.low = min(active.low, price)
                    active.close = price
                    continue

                # Candle closed → persist it
                df = self._candles[symbol]
                df.loc[len(df)] = {
                    "time": active.timestamp,
                    "open": active.open,
                    "high": active.high,
                    "low": active.low,
                    "close": active.close,
                }

                # Cleanup
                if len(df) > self.max_candles:
                    self._candles[symbol] = df.iloc[-self.max_candles :].reset_index(
                        drop=True
                    )

                # Start new active candle
                self._active[symbol] = ActiveCandle(
                    timestamp=candle_ts,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                )

    async def fetch_candles(self, symbol: str) -> pd.DataFrame:
        if self.candles_fetched[symbol]:
            async with self._lock:
                return self._candles[symbol].copy()
        else:
            # triggers fetching realtime candles from the API
            _ = await self.api.get_candles(symbol, self.timeframe, self.max_candles)
            async with self._candles_fetched_lock:
                self.candles_fetched[symbol] = True
            while True:
                async with self._lock:
                    if len(self._candles[symbol]) >= 2:
                        return self._candles[symbol].copy()
                await asyncio.sleep(1)

    async def execute(
        self, symbol: str, action: str, timeframe: int, profit_rate: int
    ) -> None:
        result = False
        counter = 0
        while not result:
            result, _ = await self.api.place_order(
                symbol, self.order_amount, action, timeframe
            )
            counter += 1
            if counter == 10:
                raise ExecutingOrderMultipleAttemptsException("Error executing orders")

    async def process_result(self, symbol: str, profit: bool) -> None:
        return


def candles_to_dataframe(candles: List[Candle]) -> pd.DataFrame:
    candles.sort(key=lambda x: x.timestamp)
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
