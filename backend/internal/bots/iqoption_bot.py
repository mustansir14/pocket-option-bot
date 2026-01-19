from typing import Dict, Any, List
import time

from iqoptionapi.stable_api import IQ_Option
import pandas as pd

from internal.bots import IBot, InvalidConnectionInfoException, BotNotConnectedException, PayoutNotFoundException

# symbols and their payouts
IQOPTION_SYMBOLS = {
    "EURUSD": 92,
    "USDJPY": 51,
    "AUDUSD": 84,
    "USDCAD": 92,
    "AUDCAD": 87,
}

class IQOptionBot(IBot):
    def __init__(self, timeframe: int, max_candles: int) -> None:
        self.timeframe = timeframe
        self.max_candles = max_candles
        self.iq_option = None

    async def connect(self, connection_info: Dict[str, Any]) -> None:
        if "username" not in connection_info or "password" not in connection_info:
            raise InvalidConnectionInfoException(
                "Missing 'username' or 'password' in connection_info"
            )
        self.iq_option = IQ_Option(connection_info["username"], connection_info["password"])
        self.iq_option.connect()
    
    async def fetch_candles(self, symbol: str) -> pd.DataFrame:
        if self.iq_option is None:
            raise BotNotConnectedException("IQ Option bot is not connected.")
        candles = self.iq_option.get_candles(symbol, self.timeframe, self.max_candles+1, time.time())
        df = pd.DataFrame(candles)
        df = df.rename(
            columns={
                "from": "time",
                "open": "open",
                "max": "high",
                "min": "low",
                "close": "close",
            }
        )
        return df[:-1]  # exclude the last candle which may be incomplete
    
    def get_available_symbols(self) -> List[str]:
        return list(IQOPTION_SYMBOLS.keys())
    
    
    def get_payout_for_symbol(self, symbol: str) -> int:
        payout = IQOPTION_SYMBOLS.get(symbol)
        if payout is None:
            raise PayoutNotFoundException(f"Payout not found for symbol: {symbol}")
        return payout