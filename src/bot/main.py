import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    if not API_TOKEN or API_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error("TELEGRAM_BOT_TOKEN is not set or is invalid. Please set it in secrets.")
        return

    logging.info("Initializing bot with token...")
    try:
        bot = Bot(token=API_TOKEN)
        dp = Dispatcher()

        @dp.message(Command("start"))
        async def cmd_start(message: Message):
            await message.answer(
                "Welcome to TaskRelay Bot!\n\n"
                "Please enter your access code to begin."
            )

        @dp.message(Command("history"))
        async def cmd_history(message: Message):
            await message.answer("Fetching job history... (Admin only)")

        logging.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
