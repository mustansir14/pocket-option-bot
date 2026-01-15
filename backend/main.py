import asyncio
import logging
from typing import Optional, Dict, Any

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, root_validator

from internal.bots import IBot, BotEnum
from internal.bots.pocketoption_bot import (
    ExecutingOrderMultipleAttemptsException,
    FetchingCandlesMultipleAttemptsException,
    PocketOptionBot,
)
from internal.env import Env
from internal.order_actions import IOrderAction, OrderActionEnum
from internal.order_actions.telegram_signal_action import TelegramSignalAction
from internal.trading_strategies import ITradingStrategy, TradingStrategyEnum
from internal.trading_strategies.last_x_candles import LastXCandlesTradingStrategy
from internal.trading_strategies.moving_average import MovingAverageTradingStrategy

# symbols and their payouts
SYMBOLS = {
    "#AAPL_otc": 92,
    "#AXP_otc": 50,
    "#BA_otc": 88,
    "#CSCO_otc": 79,
    "#INTC_otc": 56,
    "#JNJ_otc": 64,
    "#MCD_otc": 75,
    "#PFE_otc": 20,
    "#TSLA_otc": 92,
    "#XOM_otc": 42,
    "100GBP_otc": 45,
    "AUDCAD_otc": 75,
    # 'EURUSD_otc': 90 # you can comment out symbols to exclude them
}
AMOUNT = 10
MAX_MARTINGALE_ATTEMPTS = 1

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
bot: IBot = None
bot_running = False
bot_task = None
in_trade_cooldown_period = False

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
    bot_type: BotEnum
    connection_info: Dict[str, Any]
    order_action: OrderActionEnum
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
                raise ValueError("fast_period should be less than slow_period.")

        return values


rmutex = asyncio.Lock()
wmutex = asyncio.Lock()


async def main_bot_worker(
    bot_type: BotEnum,
    connection_info: Dict[str, Any],
    candles_to_check: int,
    timeframe: int,
    trading_strategy: ITradingStrategy,
    order_action: OrderActionEnum,
):
    global bot, bot_running

    if bot_type == BotEnum.POCKET_OPTION:
        bot = PocketOptionBot(AMOUNT, timeframe, candles_to_check)
    else:
        raise ValueError("Unsupported bot type")
    await bot.connect(connection_info)
    logger.info("Connected to the PocketOption API")

    if order_action == OrderActionEnum.EXECUTE_ORDER:
        order_action_obj = bot
    elif order_action == OrderActionEnum.TELEGRAM_SIGNAL:
        order_action_obj = TelegramSignalAction(
            Env.TELEGRAM_BOT_TOKEN, Env.TELEGRAM_CHAT_ID, bot
        )

    tasks = []
    for symbol, payout in SYMBOLS.items():
        task = asyncio.create_task(
            child_bot_worker(
                symbol,
                payout,
                candles_to_check,
                timeframe,
                trading_strategy,
                order_action_obj,
            )
        )
        tasks.append(task)

    await asyncio.gather(*tasks)


async def child_bot_worker(
    symbol: str,
    payout: int,
    candles_to_check: int,
    timeframe: int,
    trading_strategy: ITradingStrategy,
    order_action: IOrderAction,
):
    global bot, in_trade_cooldown_period, bot_running

    prev_data = None
    order_executed = False
    skip_next_candle = False
    current_martingale_attempt = 0

    logger.info(f"[{symbol}] Checking last {candles_to_check} candles...")

    while bot_running:
        try:
            # use mutex lock so one worker accesses the API at a time
            await asyncio.sleep(1)
            logger.info(f"[{symbol}] Fetching candles...")
            data = await bot.fetch_candles(symbol)
        except FetchingCandlesMultipleAttemptsException:
            logger.error(f"[{symbol}] Could not get candles after multiple attempts")
            async with rmutex:
                await bot.connect(bot.ssid)
            continue

        if not bot_running:
            break

        if (
            prev_data is not None
            and data["time"].iloc[-1] <= prev_data["time"].iloc[-1]
        ):
            prev_data = data
            await asyncio.sleep(2)
            continue
        prev_data = data
        logger.info(
            f"[{symbol}] Got new candle time {data['time'].iloc[-1]} open {data['open'].iloc[-1]} close {data['close'].iloc[-1]}"
        )

        if skip_next_candle:
            skip_next_candle = False
            continue

        # if there was an order executed previously, check if it was profit or loss
        if order_executed:
            is_profit = False
            if action == "call":
                if data["close"].iloc[-1] > data["open"].iloc[-1]:
                    is_profit = True
            else:
                if data["close"].iloc[-1] < data["open"].iloc[-1]:
                    is_profit = True
            logger.info(
                f'[{symbol}] Candle time {data["time"].iloc[-1]} open {data["open"].iloc[-1]} close {data["close"].iloc[-1]} -> {"profit" if is_profit else "loss"}'
            )
            if not is_profit:
                current_martingale_attempt += 1
                if current_martingale_attempt <= MAX_MARTINGALE_ATTEMPTS:
                    continue
                current_martingale_attempt = 0
            await order_action.process_result(
                symbol, is_profit, current_martingale_attempt
            )
            in_trade_cooldown_period = False
            order_executed = False

        action = trading_strategy.get_next_action(data)

        if action:
            logger.info(
                f'[{symbol}] Executing order action for {"buy" if action == "call" else "sell"}...'
            )
            try:
                # use mutex lock so one worker accesses the API at a time
                async with wmutex:
                    if not in_trade_cooldown_period:
                        await order_action.execute(symbol, action, timeframe, payout)
                        in_trade_cooldown_period = True
                        skip_next_candle = True
                        order_executed = True
                        logger.info(f"[{symbol}] Successfully executed order action")
                    else:
                        logger.info(
                            f"[{symbol}] In trade cooldown period, skipping order execution"
                        )
            except ExecutingOrderMultipleAttemptsException:
                logger.error(
                    f"[{symbol}] Could not execute order action after multiple attempts"
                )
        await asyncio.sleep(1)


async def reset_trade_cooldown(timeframe):
    global in_trade_cooldown_period
    logger.info("Starting trade cooldown period")
    await asyncio.sleep(timeframe)  # Cooldown period of expiration seconds
    in_trade_cooldown_period = False
    logger.info("Trade cooldown period ended")


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
        config.bot_type,
        config.connection_info,
        config.candles_to_check,
        config.timeframe,
        trading_strategy_class,
        config.order_action,
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
