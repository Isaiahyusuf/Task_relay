from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from src.bot.database import async_session, User
from src.bot.database.models import UserRole
from src.bot.services.access_codes import AccessCodeService
from src.bot.utils.keyboards import get_main_menu_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

class AuthStates(StatesGroup):
    waiting_for_code = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    logger.info(f"Received /start from user {message.from_user.id}")
    if not async_session:
        await message.answer("⚠️ Bot is not properly configured. Please contact an administrator.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            role_name = user.role.value.capitalize()
            keyboard = get_main_menu_keyboard(user.role)
            await message.answer(
                f"👋 Welcome back, {message.from_user.first_name or 'there'}!\n\n"
                f"You are logged in as: *{role_name}*\n\n"
                "Use the menu below to navigate:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await state.clear()
            return
    
    await message.answer(
        "🤖 *Welcome to TaskRelay Bot!*\n\n"
        "This is a workflow automation and job dispatch system.\n\n"
        "📝 Please enter your access code to begin:",
        parse_mode="Markdown"
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
    
    if success:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()
        
        if user:
            keyboard = get_main_menu_keyboard(user.role)
            await message.answer(
                f"✅ {response}\n\n"
                "Use the menu below to get started:",
                reply_markup=keyboard
            )
        else:
            await message.answer(f"✅ {response}")
        await state.clear()
    else:
        await message.answer(
            f"❌ {response}\n\n"
            "Please try again with a valid access code:"
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await show_help(message)

@router.message(F.text == "ℹ️ Help")
async def btn_help(message: Message):
    await show_help(message)

async def show_help(message: Message):
    if not async_session:
        await message.answer("⚠️ Bot is not properly configured.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                "❌ You are not registered.\n\n"
                "Please use /start to register with your access code."
            )
            return
        
        if user.role == UserRole.ADMIN:
            help_text = (
                "👑 *Admin Commands*\n\n"
                "📊 *Job History* - View all job records\n"
                "📦 *Archive Jobs* - Archive old completed jobs\n"
                "🔑 *Create Access Code* - Generate new access codes\n"
                "📋 *View Archived* - Browse archived jobs\n\n"
                "You can also use these text commands:\n"
                "`/history` - View job history\n"
                "`/archive` - Archive old jobs\n"
                "`/createcode <code> <role>` - Create access code"
            )
        elif user.role == UserRole.SUPERVISOR:
            help_text = (
                "👔 *Supervisor Commands*\n\n"
                "➕ *New Job* - Create and dispatch a new job\n"
                "📋 *My Jobs* - View jobs you've created\n\n"
                "You can also use these text commands:\n"
                "`/newjob` - Create a new job\n"
                "`/myjobs` - View your jobs"
            )
        else:
            help_text = (
                "🔧 *Subcontractor Commands*\n\n"
                "📋 *My Assigned Jobs* - View jobs assigned to you\n\n"
                "For each job, you can:\n"
                "• ✅ Accept the job\n"
                "• ❌ Decline with a reason\n"
                "• 💬 Submit a quote (for quote jobs)\n\n"
                "You can also use:\n"
                "`/jobs` - View your assigned jobs"
            )
        
        await message.answer(help_text, parse_mode="Markdown")
