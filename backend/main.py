import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from internal.bot import PocketOptionBot, FetchingCandlesMultipleAttemptsException, ExecutingOrderMultipleAttemptsException

SYMBOL = "#AXP_otc"
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
bot_running = False
bot_task = None
api = None

# Configure the logger
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)

# Stream handler for console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class BotConfig(BaseModel):
    ssid: str
    candles_to_check: int
    timeframe: int


async def bot_worker(ssid: str, candles_to_check: int, timeframe: int):
    global api, bot_running

    bot = PocketOptionBot()
    await bot.connect(ssid)
    logger.info("Connected to the PocketOption API")

    prev_data = None

    logger.info(f"Checking last {candles_to_check} candles...")

    while bot_running:
        try:
            data = await bot.fetch_candles(SYMBOL, timeframe, candles_to_check)
        except FetchingCandlesMultipleAttemptsException:
            logger.error("Could not get candles after multiple attempts")
            break

        if not bot_running:
            break

        if prev_data is not None and data["time"].iloc[-1] == prev_data["time"].iloc[-1]:
            prev_data = data
            await asyncio.sleep(1)
            continue

        logger.info("Got new candle")

        prev_data = data

        if all(data['close'] < data['open']):
            action = "call"
        elif all(data['close'] > data['open']):
            action = "put"
        else:
            action = ""

        if action:
            logger.info(
                f'Creating order for {"buy" if action == "call" else "sell"}...')
            try:
                await bot.execute_order(AMOUNT, SYMBOL, action, EXPIRATION_SECONDS)
            except ExecutingOrderMultipleAttemptsException:
                logger.error(
                    "Could not create order after multiple attempts")
                continue

            logger.info("Successfully created order")

        await asyncio.sleep(1)


@app.post("/start-bot")
async def start_bot(config: BotConfig, background_tasks: BackgroundTasks):
    global bot_running, bot_task
    if bot_running:
        raise HTTPException(status_code=400, detail="Bot is already running")

    bot_running = True
    bot_task = background_tasks.add_task(
        bot_worker, config.ssid, config.candles_to_check, config.timeframe)
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
