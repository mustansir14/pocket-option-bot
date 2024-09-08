import asyncio
import logging
from typing import Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, root_validator

from internal.bot import (ExecutingOrderMultipleAttemptsException,
                          FetchingCandlesMultipleAttemptsException,
                          PocketOptionBot)
from internal.trading_strategies import ITradingStrategy, TradingStrategyEnum
from internal.trading_strategies.last_x_candles import \
    LastXCandlesTradingStrategy
from internal.trading_strategies.moving_average import \
    MovingAverageTradingStrategy

SYMBOLS = [
    "#AAPL_otc",
    "#AXP_otc",
    "#BA_otc",
    "#CSCO_otc",
    "#FB_otc",
    "#INTC_otc",
    "#JNJ_otc",
    "#MCD_otc",
    "#MSFT_otc",
    "#PFE_otc",
    "#TSLA_otc",
    "#XOM_otc",
    "100GBP_otc",
    "AMZN_otc",
    "AUDCAD_otc"
    # 'EURUSD_otc' # you can comment out symbols to exclude them
]
AMOUNT = 10
EXPIRATION_SECONDS = 60

app = FastAPI()

# Allow all CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define the bot state and variables
bot: PocketOptionBot = None
bot_running = False
bot_task = None

# Configure the logger
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)

# Stream handler for console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class BotConfig(BaseModel):
    ssid: str
    trading_strategy: TradingStrategyEnum
    candles_to_check: Optional[int] = None
    fast_period: Optional[int] = None
    slow_period: Optional[int] = None
    timeframe: int

    # Custom validation logic
    @root_validator(pre=True)
    def check_trading_strategy(cls, values):
        trading_strategy = values.get("trading_strategy")

        if trading_strategy == TradingStrategyEnum.LAST_X_CANDLES:
            candles_to_check = values.get("candles_to_check")
            if not candles_to_check:
                raise ValueError(
                    "candles_to_check is required for LAST_X_CANDLES strategy."
                )

        if trading_strategy == TradingStrategyEnum.MOVING_AVERAGE:
            fast_period = values.get("fast_period")
            slow_period = values.get("slow_period")
            if fast_period is None or slow_period is None:
                raise ValueError(
                    "Both fast_period and slow_period are required for MOVING_AVERAGE strategy."
                )
            if fast_period >= slow_period:
                raise ValueError(
                    "fast_period should be less than slow_period.")

        return values


mutex = asyncio.Lock()


async def main_bot_worker(
    ssid: str, candles_to_check: int, timeframe: int, trading_strategy: ITradingStrategy
):
    global bot, bot_running

    bot = PocketOptionBot()
    await bot.connect(ssid)
    logger.info("Connected to the PocketOption API")

    tasks = []
    for symbol in SYMBOLS:
        task = asyncio.create_task(
            child_bot_worker(symbol, candles_to_check,
                             timeframe, trading_strategy)
        )
        tasks.append(task)

    await asyncio.gather(*tasks)


async def child_bot_worker(
    symbol: str,
    candles_to_check: int,
    timeframe: int,
    trading_strategy: ITradingStrategy,
):
    global bot

    prev_data = None

    logger.info(f"[{symbol}] Checking last {candles_to_check} candles...")

    while bot_running:
        try:
            # use mutex lock so one worker accesses the API at a time
            async with mutex:
                await asyncio.sleep(1)
                data = await bot.fetch_candles(symbol, timeframe, candles_to_check)
        except FetchingCandlesMultipleAttemptsException:
            logger.error(
                f"[{symbol}] Could not get candles after multiple attempts")
            async with mutex:
                await bot.connect(bot.ssid)
            continue

        if not bot_running:
            break

        if (
            prev_data is not None
            and data["time"].iloc[-1] == prev_data["time"].iloc[-1]
        ):
            prev_data = data
            await asyncio.sleep(2)
            continue
        prev_data = data

        logger.info(f"[{symbol}] Got new candle")

        action = trading_strategy.get_next_action(data)

        if action:
            logger.info(
                f'[{symbol}] Creating order for {"buy" if action == "call" else "sell"}...'
            )
            try:
                # use mutex lock so one worker accesses the API at a time
                async with mutex:
                    await bot.execute_order(AMOUNT, symbol, action, EXPIRATION_SECONDS)
            except ExecutingOrderMultipleAttemptsException:
                logger.error(
                    f"[{symbol}] Could not create order after multiple attempts"
                )
                continue

            logger.info(f"[{symbol}] Successfully created order")

        await asyncio.sleep(1)


@app.post("/start-bot")
async def start_bot(config: BotConfig, background_tasks: BackgroundTasks):
    global bot_running, bot_task
    if bot_running:
        raise HTTPException(status_code=400, detail="Bot is already running")

    if config.trading_strategy == TradingStrategyEnum.LAST_X_CANDLES:
        trading_strategy_class = LastXCandlesTradingStrategy()
    elif config.trading_strategy == TradingStrategyEnum.MOVING_AVERAGE:
        trading_strategy_class = MovingAverageTradingStrategy(
            config.fast_period, config.slow_period
        )
        config.candles_to_check = config.slow_period + 1

    bot_running = True
    bot_task = background_tasks.add_task(
        main_bot_worker,
        config.ssid,
        config.candles_to_check,
        config.timeframe,
        trading_strategy_class,
    )
    return {"status": "Bot started"}


@app.post("/stop-bot")
async def stop_bot():
    global bot_running, bot_task
    if not bot_running:
        raise HTTPException(status_code=400, detail="Bot is not running")

    bot_running = False
    bot_task = None
    return {"status": "Bot stopped"}


@app.get("/bot-status")
async def bot_status():
    global bot_running
    return {"bot_running": bot_running}


if __name__ == "__main__":
    uvicorn.run(app)
