from datetime import datetime
from sqlalchemy import select
from src.bot.database import async_session, AccessCode, User, Team
from src.bot.database.models import UserRole
import logging

logger = logging.getLogger(__name__)

class AccessCodeService:
    @staticmethod
    async def validate_code(code: str) -> AccessCode | None:
        if not async_session:
            return None
        async with async_session() as session:
            result = await session.execute(
                select(AccessCode).where(AccessCode.code == code)
            )
            access_code = result.scalar_one_or_none()
            
            if not access_code:
                return None
            
            if not access_code.is_active:
                return None
            
            if access_code.max_uses and access_code.current_uses >= access_code.max_uses:
                return None
            
            if access_code.expires_at and access_code.expires_at < datetime.utcnow():
                return None
            
            return access_code
    
    @staticmethod
    async def register_user(telegram_id: int, username: str | None, first_name: str | None, code: str) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not configured"
        
        async with async_session() as session:
            existing_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            existing_user = existing_result.scalar_one_or_none()
            
            if existing_user and existing_user.is_active:
                return False, "You are already registered."
            
            result = await session.execute(
                select(AccessCode).where(AccessCode.code == code)
            )
            access_code = result.scalar_one_or_none()
            
            if not access_code:
                return False, "Invalid access code."
            
            if not access_code.is_active:
                return False, "This access code is no longer active."
            
            if access_code.max_uses and access_code.current_uses >= access_code.max_uses:
                return False, "This access code has reached its usage limit."
            
            if access_code.expires_at and access_code.expires_at < datetime.utcnow():
                return False, "This access code has expired."
            
            if existing_user:
                existing_user.is_active = True
                existing_user.role = access_code.role
                existing_user.team_id = access_code.team_id
                existing_user.access_code_id = access_code.id
                existing_user.username = username
                existing_user.first_name = first_name
            else:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    role=access_code.role,
                    team_id=access_code.team_id,
                    access_code_id=access_code.id
                )
                session.add(user)
            
            access_code.current_uses += 1
            
            await session.commit()
            
            role_name = access_code.role.value.capitalize()
            return True, f"Welcome! You have been registered as a {role_name}."
    
    @staticmethod
    async def create_bootstrap_codes(codes: list[str], team_name: str = "Default"):
        if not async_session or not codes:
            return
        
        async with async_session() as session:
            team_result = await session.execute(
                select(Team).where(Team.name == team_name)
            )
            team = team_result.scalar_one_or_none()
            
            if not team:
                team = Team(name=team_name)
                session.add(team)
                await session.flush()
            
            for code in codes:
                existing = await session.execute(
                    select(AccessCode).where(AccessCode.code == code)
                )
                if not existing.scalar_one_or_none():
                    access_code = AccessCode(
                        code=code,
                        role=UserRole.ADMIN,
                        team_id=team.id,
                        max_uses=1,
                        is_active=True
                    )
                    session.add(access_code)
                    logger.info(f"Created bootstrap admin code: {code[:4]}***")
            
            await session.commit()
    
    @staticmethod
    async def create_access_code(code: str, role: UserRole, team_id: int | None = None, max_uses: int = 1) -> bool:
        if not async_session:
            return False
        
        async with async_session() as session:
            existing = await session.execute(
                select(AccessCode).where(AccessCode.code == code)
            )
            if existing.scalar_one_or_none():
                return False
            
            access_code = AccessCode(
                code=code,
                role=role,
                team_id=team_id,
                max_uses=max_uses,
                is_active=True
            )
            session.add(access_code)
            await session.commit()
            return True
