import logging
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Bot, Dispatcher
from src.bot.config import config
from src.bot.database import init_db
from src.bot.database.session import engine
from src.bot.services.access_codes import AccessCodeService
from src.bot.handlers import auth_router, supervisor_router, subcontractor_router, admin_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    config.setup_logging()
    
    if not config.validate():
        logger.error("Configuration validation failed. Exiting.")
        return
    
    if not engine:
        logger.error("Database engine not initialized. Check DATABASE_URL.")
        return
    
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Setting up bootstrap admin codes...")
    await AccessCodeService.create_bootstrap_codes(config.ADMIN_BOOTSTRAP_CODES)
    
    logger.info("Initializing bot...")
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(auth_router)
    dp.include_router(supervisor_router)
    dp.include_router(subcontractor_router)
    dp.include_router(admin_router)
    
    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
