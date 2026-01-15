import asyncio
import logging
from datetime import datetime, timedelta

from telegram import Bot

from internal.bot import PocketOptionBot
from internal.order_actions import IOrderAction


def asset_parse(asset: str) -> str:
    if asset.endswith("_otc"):
        base = asset.replace("_otc", "")
        if len(base) >= 6 and "/" not in base and not base.startswith("#"):
            return f"{base[:3]}/{base[3:]} (OTC)"
        return f"{base} (OTC)"
    if len(asset) >= 6 and "/" not in asset and not asset.startswith("#"):
        return f"{asset[:3]}/{asset[3:]}"
    return asset


class TelegramSignalAction(IOrderAction):
    def __init__(
        self,
        token: str,
        chat_id: str,
        pocketoption_bot: PocketOptionBot,
    ) -> None:
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        self.pocketoption_bot = pocketoption_bot
        self.symbol_to_message_id = {}

    async def execute(
        self, symbol: str, action: str, timeframe: int, profit_rate: int
    ) -> None:
        entry_time = datetime.now() + timedelta(seconds=timeframe)
        entry_time_formatted = entry_time.strftime("%H:%M")

        parsed_symbol = asset_parse(symbol)  # ✅ always define it

        if action == "call":
            signal = "🟢 CALL UP ⬆️"
        else:
            signal = "🔴 PUT DOWN ⬇️"

        message = f"""
🚧 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐏𝐎 𝐓𝐑𝐀𝐃𝐄 🚧
━━━━━━━━━━━━━━━
📊 {parsed_symbol}
⏰ {entry_time_formatted}
⌛️ {seconds_to_formatted_time(timeframe)}
{signal}
━━━━━━━━━━━━━━━
▫️𝗔𝗜 𝗦𝗶𝗴𝗻𝗮𝗹: Pattern Detection
▫️𝐏𝐫𝐨𝐟𝐢𝐭 𝐑𝐚𝐭𝐞: {profit_rate}%
━━━━━━━━━━━━━━━
🛜 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗯𝘆: 𝗣𝗵𝗮𝗻𝘁𝗼𝗺 𝗔𝗜
"""
        message = await self.bot.send_message(
            chat_id=self.chat_id, text=message, write_timeout=30, parse_mode="HTML"
        )
        self.symbol_to_message_id[symbol] = message.message_id

    async def process_result(self, symbol: str, profit: bool, martingale: int) -> None:
        message_id = self.symbol_to_message_id.get(symbol)
        if message_id is None:
            return

        parsed_symbol = asset_parse(symbol)

        # Result label
        if profit:
            result_text = "Profit ✅"
            if martingale > 0:
                message += f" (Martingale {martingale})"
        else:
            # this loss happens after MG1 (attempt=1) in your logic
            result_text = "Loss ☑️"

        message = f"🗓 {parsed_symbol} {result_text}"

        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            write_timeout=30,
            parse_mode="HTML",
            reply_to_message_id=message_id,
        )


def seconds_to_formatted_time(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    minutes_str = "Minutes"
    if minutes == 1:
        minutes_str = "Minute"
    hours_str = "Hours"
    if hours == 1:
        hours_str = "Hour"
    seconds_str = "Seconds"
    if sec == 1:
        seconds_str = "Second"
    if hours > 0:
        if minutes > 0:
            return f"{hours} {hours_str} {minutes} {minutes_str}"
        return f"{hours} {hours_str}"
    elif minutes > 0:
        if sec > 0:
            return f"{minutes} {minutes_str} {sec} {seconds_str}"
        return f"{minutes} {minutes_str}"
    else:
        return f"{sec} {seconds_str}"
