from sqlalchemy import select
from src.bot.database import async_session, User
from src.bot.database.models import AvailabilityStatus
import logging

logger = logging.getLogger(__name__)

class AvailabilityService:
    @staticmethod
    async def set_availability(telegram_id: int, status: AvailabilityStatus) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not available"
        
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            user.availability_status = status
            await session.commit()
            
            status_text = {
                AvailabilityStatus.AVAILABLE: "Available",
                AvailabilityStatus.BUSY: "Busy",
                AvailabilityStatus.AWAY: "Away"
            }.get(status, "Unknown")
            
            return True, f"Your status is now: {status_text}"
    
    @staticmethod
    async def get_availability(telegram_id: int) -> AvailabilityStatus | None:
        if not async_session:
            return None
        
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            return user.availability_status
