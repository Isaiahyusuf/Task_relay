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
            keyboard = get_main_menu_keyboard(user.role)
            await message.answer(
                f"Welcome back, {message.from_user.first_name or 'there'}!\n\n"
                f"You are logged in as: *{role_name}*\n\n"
                "Use the menu below to navigate:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await state.clear()
            return
    
    await message.answer(
        "*Welcome to TaskRelay Bot!*\n\n"
        "This is a workflow automation and job dispatch system.\n\n"
        "Please enter your access code to begin:",
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
                f"{response}\n\n"
                "Use the menu below to get started:",
                reply_markup=keyboard
            )
        else:
            await message.answer(response)
        await state.clear()
    else:
        await message.answer(
            f"{response}\n\n"
            "Please try again with a valid access code:"
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await show_help(message)

@router.message(F.text == "ℹ️ Help")
async def btn_help(message: Message):
    await show_help(message)

@router.message(F.text == "📘 About")
async def btn_about(message: Message):
    about_text = (
        "🤖 *About TaskRelay Bot*\n\n"
        "TaskRelay is a workflow automation system designed to streamline job dispatch "
        "and management between Supervisors and Subcontractors.\n\n"
        "🌟 *Key Features:*\n"
        "• *Real-time Dispatch:* Instant job notifications for subcontractors.\n"
        "• *Quote System:* Subcontractors can bid on jobs; supervisors select the best offer.\n"
        "• *Availability Tracking:* Toggle your status (Available/Busy/Away) to control job flow.\n"
        "• *Automated Reminders:* Never miss a deadline with automated status pings.\n"
        "• *Full History:* Track jobs from creation to completion with detailed timestamps.\n\n"
        "🚀 *Role-Based Access:*\n"
        "• *Supervisors:* Create jobs, manage quotes, and track team progress.\n"
        "• *Subcontractors:* Accept jobs, submit quotes, and update work status.\n"
        "• *Admins:* Manage access codes and system archives.\n\n"
        "_Version 1.0.0 - Streamlining your workflow._"
    )
    await message.answer(about_text, parse_mode="Markdown")

async def show_help(message: Message):
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
                "You are not registered.\n\n"
                "Please use /start to register with your access code."
            )
            return
        
        if user.role == UserRole.ADMIN:
            help_text = (
                "*Admin Commands*\n\n"
                "*Job History* - View all job records\n"
                "*Archive Jobs* - Archive old completed jobs\n"
                "*Create Access Code* - Generate new access codes\n"
                "*View Archived* - Browse archived jobs"
            )
        elif user.role == UserRole.SUPERVISOR:
            help_text = (
                "*Supervisor Commands*\n\n"
                "*New Job* - Create and send a new job\n"
                "*My Jobs* - View all your jobs\n"
                "*Pending Jobs* - View created/sent jobs\n"
                "*Active Jobs* - View accepted/in-progress jobs\n\n"
                "*Job Actions:*\n"
                "- View Details\n"
                "- View Quotes (for quote jobs)\n"
                "- Cancel Job\n"
                "- Mark Complete"
            )
        else:
            help_text = (
                "*Subcontractor Commands*\n\n"
                "*Available Jobs* - View jobs waiting for response\n"
                "*My Active Jobs* - View accepted/in-progress jobs\n\n"
                "*Availability Status:*\n"
                "- Available - Receive new jobs\n"
                "- Busy - Temporarily unavailable\n"
                "- Away - Not accepting jobs\n\n"
                "*Job Actions:*\n"
                "- Accept job\n"
                "- Decline with reason\n"
                "- Submit quote (for quote jobs)\n"
                "- Start job\n"
                "- Mark complete"
            )
        
        await message.answer(help_text, parse_mode="Markdown")
