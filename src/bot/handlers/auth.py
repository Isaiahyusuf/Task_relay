from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select
from src.bot.database import async_session, User
from src.bot.services.access_codes import AccessCodeService
import logging

logger = logging.getLogger(__name__)
router = Router()

class AuthStates(StatesGroup):
    waiting_for_code = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    if not async_session:
        await message.answer("Bot is not properly configured. Please contact an administrator.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            role_name = user.role.value.capitalize()
            await message.answer(
                f"Welcome back! You are logged in as a {role_name}.\n\n"
                "Available commands:\n"
                "/help - Show available commands"
            )
            await state.clear()
            return
    
    await message.answer(
        "Welcome to TaskRelay Bot!\n\n"
        "This is a workflow automation and job dispatch system.\n\n"
        "Please enter your access code to begin:"
    )
    await state.set_state(AuthStates.waiting_for_code)

@router.message(StateFilter(AuthStates.waiting_for_code))
async def process_access_code(message: Message, state: FSMContext):
    code = message.text.strip()
    
    success, response = await AccessCodeService.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        code=code
    )
    
    await message.answer(response)
    
    if success:
        await state.clear()
        await message.answer(
            "You can now use the bot. Type /help to see available commands."
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    if not async_session:
        await message.answer("Bot is not properly configured.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                "You are not registered. Please use /start to register with your access code."
            )
            return
        
        from src.bot.database.models import UserRole
        
        base_commands = "/start - Start bot and authenticate\n/help - Show this help message"
        
        if user.role == UserRole.ADMIN:
            role_commands = (
                "\n\nAdmin Commands:\n"
                "/history - View job history\n"
                "/archive - Manually archive old jobs\n"
                "/createcode <code> <role> - Create access code (role: admin/supervisor/subcontractor)"
            )
        elif user.role == UserRole.SUPERVISOR:
            role_commands = (
                "\n\nSupervisor Commands:\n"
                "/newjob - Create a new job\n"
                "/myjobs - View your created jobs"
            )
        else:
            role_commands = (
                "\n\nSubcontractor Commands:\n"
                "/jobs - View assigned jobs\n"
                "/accept <job_id> - Accept a job\n"
                "/decline <job_id> - Decline a job"
            )
        
        await message.answer(base_commands + role_commands)
