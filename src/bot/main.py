import logging
import asyncio
import signal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from src.bot.config import config
from src.bot.database import init_db
from src.bot.database.session import engine
from src.bot.services.access_codes import AccessCodeService
from src.bot.services.scheduler import SchedulerService
from src.bot.handlers import auth_router, supervisor_router, subcontractor_router, admin_router
from src.bot.middleware.error_handler import setup_error_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

bot: Bot | None = None
dp: Dispatcher | None = None
scheduler_task: asyncio.Task | None = None

async def shutdown(sig=None):
    global scheduler_task
    
    if sig:
        logger.info(f"Received signal {sig.name}, shutting down...")
    else:
        logger.info("Shutting down...")
    
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
    
    if dp:
        await dp.stop_polling()
    
    if bot:
        await bot.session.close()
    
    if engine:
        await engine.dispose()
    
    logger.info("Shutdown complete")

def handle_signal(sig):
    asyncio.create_task(shutdown(sig))

async def main():
    global bot, dp, scheduler_task
    
    config.setup_logging()
    
    if not config.validate():
        logger.error("Configuration validation failed. Exiting.")
        sys.exit(1)
    
    if not engine:
        logger.error("Database engine not initialized. Check DATABASE_URL.")
        sys.exit(1)
    
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    logger.info("Setting up bootstrap admin codes...")
    try:
        await AccessCodeService.create_bootstrap_codes(config.ADMIN_BOOTSTRAP_CODES)
    except Exception as e:
        logger.warning(f"Failed to create bootstrap codes: {e}")
    
    logger.info("Initializing bot...")
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    SchedulerService.set_bot(bot)
    
    setup_error_handlers(dp)
    
    dp.include_router(auth_router)
    dp.include_router(supervisor_router)
    dp.include_router(subcontractor_router)
    dp.include_router(admin_router)
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))
        except NotImplementedError:
            pass
    
    scheduler_task = asyncio.create_task(SchedulerService.run_scheduler())
    
    logger.info("Starting bot polling...")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Reminder hours: {config.RESPONSE_REMINDER_HOURS}")
    logger.info(f"Auto-close hours: {config.JOB_AUTO_CLOSE_HOURS}")
    
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Polling error: {e}")
    finally:
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
