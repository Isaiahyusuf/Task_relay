from functools import wraps
from aiogram.types import Message
from sqlalchemy import select
from src.bot.database import async_session, User
from src.bot.database.models import UserRole
import logging

logger = logging.getLogger(__name__)

async def get_user_role(telegram_id: int) -> UserRole | None:
    if not async_session:
        return None
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        return user.role if user else None

async def get_user(telegram_id: int) -> User | None:
    if not async_session:
        return None
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id, User.is_active == True)
        )
        return result.scalar_one_or_none()

def require_role(*roles: UserRole):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: Message, *args, **kwargs):
            user_role = await get_user_role(message.from_user.id)
            if user_role is None:
                await message.answer("You are not registered. Please use /start with your access code.")
                return
            # Super admin can access all admin routes
            allowed_roles = list(roles)
            if UserRole.ADMIN in roles and UserRole.SUPER_ADMIN not in roles:
                allowed_roles.append(UserRole.SUPER_ADMIN)
            if user_role not in allowed_roles:
                await message.answer("You don't have permission to use this command.")
                return
            return await handler(message, *args, **kwargs)
        return wrapper
    return decorator
