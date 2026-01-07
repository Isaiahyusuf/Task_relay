from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from src.bot.database import async_session, User
from src.bot.database.models import UserRole
from src.bot.services.jobs import JobService
from src.bot.services.archive import ArchiveService
from src.bot.services.access_codes import AccessCodeService
from src.bot.utils.permissions import require_role
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("history"))
@require_role(UserRole.ADMIN)
async def cmd_history(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    jobs = await JobService.get_job_history(team_id=user.team_id if user else None)
    
    if not jobs:
        await message.answer("No job history found.")
        return
    
    history_lines = []
    for job in jobs:
        line = (
            f"#{job.id}: {job.title}\n"
            f"  Status: {job.status.value} | Type: {job.job_type.value}\n"
            f"  Created: {job.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        history_lines.append(line)
    
    await message.answer("Job History (last 50):\n\n" + "\n\n".join(history_lines))

@router.message(Command("archive"))
@require_role(UserRole.ADMIN)
async def cmd_archive(message: Message):
    count = await ArchiveService.archive_old_jobs()
    
    if count > 0:
        await message.answer(f"Archived {count} old jobs.")
    else:
        await message.answer("No jobs eligible for archiving.")

@router.message(Command("archived"))
@require_role(UserRole.ADMIN)
async def cmd_archived(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    jobs = await ArchiveService.get_archived_jobs(team_id=user.team_id if user else None)
    
    if not jobs:
        await message.answer("No archived jobs found.")
        return
    
    archive_lines = []
    for job in jobs:
        line = (
            f"#{job.id}: {job.title}\n"
            f"  Status: {job.status.value}\n"
            f"  Archived: {job.archived_at.strftime('%Y-%m-%d %H:%M') if job.archived_at else 'N/A'}"
        )
        archive_lines.append(line)
    
    await message.answer("Archived Jobs:\n\n" + "\n\n".join(archive_lines))

@router.message(Command("createcode"))
@require_role(UserRole.ADMIN)
async def cmd_create_code(message: Message):
    parts = message.text.split()
    
    if len(parts) < 3:
        await message.answer(
            "Usage: /createcode <code> <role>\n"
            "Roles: admin, supervisor, subcontractor\n\n"
            "Example: /createcode ABC123 supervisor"
        )
        return
    
    code = parts[1]
    role_str = parts[2].lower()
    
    role_map = {
        "admin": UserRole.ADMIN,
        "supervisor": UserRole.SUPERVISOR,
        "subcontractor": UserRole.SUBCONTRACTOR
    }
    
    if role_str not in role_map:
        await message.answer("Invalid role. Use: admin, supervisor, or subcontractor")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    success = await AccessCodeService.create_access_code(
        code=code,
        role=role_map[role_str],
        team_id=user.team_id if user else None
    )
    
    if success:
        await message.answer(f"Access code '{code}' created for role '{role_str}'.")
    else:
        await message.answer("Failed to create code. It may already exist.")
