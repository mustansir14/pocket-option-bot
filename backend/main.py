import logging
import queue
from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pocketoptionapi.stable_api import PocketOption
import asyncio

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
log_queue = queue.Queue()

# Configure the logger
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)

# Stream handler for console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Queue handler to capture logs for the WebSocket
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

queue_handler = QueueHandler(log_queue)
queue_handler.setFormatter(formatter)
logger.addHandler(queue_handler)


class BotConfig(BaseModel):
    ssid: str
    candles_to_check: int
    timeframe: int

async def bot_worker(ssid: str, candles_to_check: int, timeframe: int):
    global api, bot_running
    api = PocketOption(ssid)
    api.connect()
    while not api.check_connect():
        await asyncio.sleep(1)
    logger.info("Connected to the PocketOption API")

    ASSET = "#AXP_otc"
    prev_data = None

    logger.info(f"Checking last {candles_to_check} candles...")

    while bot_running:
        data = None
        counter = 0
        while data is None:
            data = await api.get_candles(ASSET, timeframe, None, timeframe * candles_to_check)
            if not bot_running:
                break
            counter += 1
            if counter == 5:
                logger.error("Could not get candles after multiple attempts")
                break
        if counter == 5:
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
            logger.info(f'Creating order for {"buy" if action == "call" else "sell"}...')
            result = False
            counter = 0
            while not result:
                result, _ = await api.buy(10, ASSET, action, 60)
                counter += 1
                if counter == 10:
                    logger.error("Could not create order after multiple attempts")
                    break
            if counter == 10:
                continue

            logger.info("Successfully created order")

        await asyncio.sleep(1)

@app.post("/start-bot")
async def start_bot(config: BotConfig, background_tasks: BackgroundTasks):
    global bot_running, bot_task
    if bot_running:
        raise HTTPException(status_code=400, detail="Bot is already running")

    bot_running = True
    bot_task = background_tasks.add_task(bot_worker, config.ssid, config.candles_to_check, config.timeframe)
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