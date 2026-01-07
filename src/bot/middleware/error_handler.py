from aiogram import Dispatcher
from aiogram.types import Update, ErrorEvent
import logging

logger = logging.getLogger(__name__)

async def global_error_handler(event: ErrorEvent):
    logger.error(
        f"Error handling update: {event.exception}",
        exc_info=event.exception,
        extra={
            "update_id": event.update.update_id if event.update else None,
        }
    )
    
    update = event.update
    exception = event.exception
    
    try:
        message = None
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        
        if message:
            await message.answer(
                "⚠️ An error occurred while processing your request.\n"
                "Please try again or contact support if the issue persists."
            )
    except Exception as e:
        logger.error(f"Failed to send error message to user: {e}")
    
    return True

def setup_error_handlers(dp: Dispatcher):
    dp.errors.register(global_error_handler)
    logger.info("Error handlers registered")
