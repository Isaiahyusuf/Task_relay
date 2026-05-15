from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from src.bot.database import async_session, User
from src.bot.database.models import UserRole
from src.bot.services.access_codes import AccessCodeService
from src.bot.utils.keyboards import get_main_menu_keyboard, get_self_delete_confirm_keyboard
from src.bot.utils.roles import role_display_name
from src.bot.config import config
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
        
        if user and user.is_active:
            # Check if super admin code is still valid
            if user.role == UserRole.SUPER_ADMIN:
                if not config.SUPER_ADMIN_CODE or user.super_admin_code != config.SUPER_ADMIN_CODE:
                    # Super admin code has changed, invalidate this user
                    user.is_active = False
                    user.role = UserRole.SUBCONTRACTOR  # Reset to lowest role
                    await session.commit()
                    await message.answer(
                        "*Access Revoked*\n\n"
                        "Your super admin access has been revoked because the access code was changed.\n\n"
                        "Please enter a new access code to continue:",
                        parse_mode="Markdown"
                    )
                    await state.set_state(AuthStates.waiting_for_code)
                    return
            
            role_name = role_display_name(user.role)
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

@router.message(F.text == "Help")
async def btn_help(message: Message):
    await show_help(message)

@router.message(F.text == "Delete My Account")
async def btn_delete_account(message: Message):
    if not async_session:
        await message.answer("Database not available.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("You are not registered.")
            return
    
    await message.answer(
        " *Delete Your Account*\n\n"
        "Are you sure you want to delete your account?\n\n"
        "*This action cannot be undone.*\n"
        "You will need a new access code to register again.",
        reply_markup=get_self_delete_confirm_keyboard(user.id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("confirm_self_delete:"))
async def handle_confirm_self_delete(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id, User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("User not found", show_alert=True)
            return
        
        if user.access_code_id:
            from src.bot.database import AccessCode
            code_result = await session.execute(
                select(AccessCode).where(AccessCode.id == user.access_code_id)
            )
            access_code = code_result.scalar_one_or_none()
            if access_code and access_code.current_uses > 0:
                access_code.current_uses -= 1
        
        user.is_active = False
        await session.commit()
    
    await callback.message.edit_text(
        "Your account has been deleted.\n\n"
        "Use /start with a new access code to register again."
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_self_delete")
async def handle_cancel_self_delete(callback: CallbackQuery):
    await callback.message.edit_text("Account deletion cancelled.")
    await callback.answer()

@router.message(F.text == "About")
async def btn_about(message: Message):
    about_text = (
        "*About TaskRelay Bot*\n\n"
        "TaskRelay is a Telegram workflow platform for Australian teams that manage field jobs from request to completion.\n\n"
        "*What It Handles*\n"
        "- Job dispatch (quote jobs and preset-price jobs)\n"
        "- Team-based assignment and visibility\n"
        "- Safety checklist submission and review\n"
        "- Availability tracking and broadcast messaging\n"
        "- Access-code based onboarding\n\n"
        "*Job Status Flow*\n"
        "- CREATED: Drafted and not yet sent\n"
        "- SENT: Available to target subcontractor(s)\n"
        "- ACCEPTED: Taken by a subcontractor\n"
        "- IN_PROGRESS: Work has started\n"
        "- SUBMITTED: Sent for supervisor review\n"
        "- COMPLETED: Closed\n"
        "- CANCELLED or ARCHIVED: Closed out\n\n"
        "*Safety Flow*\n"
        "Subcontractors can submit Site Safety Checklists from the menu and choose the supervisor recipient. Managers and supervisors can review, filter, and export submissions.\n\n"
        "*Time Zone*\n"
        "User-facing checklist and PDF times are shown in Australian local time.\n\n"
        "_TaskRelay - Operations first, chat-native workflow._"
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
        
                "*GENERAL MANAGER HELP*\n\n"
                "*Daily Use*\n"
                "- `Job History` and `Archive Jobs` for operational tracking\n"
                "- `Safety Submissions`, `Filter Safety Submissions`, `Export Safety CSV` for compliance\n"
                "- `Send Message` for announcements\n\n"
                "*People and Access*\n"
                "- `Create Manager Code`, `Create Supervisor Code`, `Create Subcontractor Code`\n"
                "- `All Access Codes` for visibility\n"
                "- `Manage Access Codes` to delete codes when needed\n"
                "- `View Managers`, `View Supervisors`, `View Subcontractors`, `All Users`\n\n"
                "*Structure and Governance*\n"
                "- `View By Teams`, `Manage Teams`\n"
                "- `View Regions`, `Manage Regions`\n"
                "- `Manage Roles`\n\n"
                "*Tip*\n"
                "Use `Switch Role` only for testing role views."
                " *View Archived* - Browse archived jobs\n\n"
                
                "*COMMUNICATION*\n"
                "*MANAGER HELP*\n\n"
                "*Jobs*\n"
                "- `New Job` to dispatch quote or preset-price work\n"
                "- `Job History`, `Archive Jobs`, `View Archived` for tracking\n\n"
                "*Safety*\n"
                "- `Request Safety Checklist` when you need a submission from a subcontractor\n"
                "- `Safety Submissions`, `Filter Safety Submissions`, `Export Safety CSV`\n\n"
                "*Team and Access*\n"
                "- `Create Access Code` for supervisor/subcontractor onboarding\n"
                "- `Manage Access Codes` to remove codes\n"
                "- `Manage Users`, `Manage Teams`, `Manage Regions`, `View By Teams`\n\n"
                "*Communication*\n"
                "- `Send Message` and `Weekly Availability`\n"
                "- Use `Switch Role` only to test menu behavior."
                "1. Tap *New Job*\n"
                "2. Choose job type (Quote or Preset Price)\n"
                "3. Enter job title and description\n"
                "*SUPERVISOR HELP*\n\n"
                "*Create and Send Work*\n"
                "- `New Job` then choose Quote or Preset Price\n"
                "- Add address/photos/deadline as needed\n\n"
                "*Track Work*\n"
                "- `My Jobs`, `Pending Jobs`, `Active Jobs`, `Submitted Jobs`\n"
                "- Use job actions to review, request revisions, or complete\n\n"
                "*Safety*\n"
                "- `Request Safety Checklist` to prompt subcontractor submission\n"
                "- `Safety Submissions`, `Filter Safety Submissions`, `Export Safety CSV`\n\n"
                "*People and Communication*\n"
                "- `Create Subcontractor Code`\n"
                "- `Manage Access Codes` to remove codes you created\n"
                "- `Send Message` and `View Availability` for coordination"
                " *Accept Quote* - Select winning quote\n"
                " *Cancel Job* - Cancel unstarted jobs\n"
                " *Mark Complete* - Close completed jobs\n"
                "*SUBCONTRACTOR HELP*\n\n"
                "*Jobs*\n"
                "- `Available Jobs` to see jobs sent to you\n"
                "- `My Active Jobs` and `Start Work` for accepted jobs\n"
                "- `Submit Job` with photos when work is done\n\n"
                "*Safety*\n"
                "- `Site Safety Checklist` can be submitted from menu\n"
                "- Choose the supervisor recipient during checklist flow\n"
                "- `My Submissions` shows your checklist history\n\n"
                "*Availability*\n"
                "- Set live status: `Available`, `Busy`, `Away`\n"
                "- Update weekly schedule in `My Availability`\n"
                "- Use `Report Unavailability` for planned time off\n\n"
                "*Communication*\n"
                "- `Contact Supervisor` or message actions when prompted\n\n"
                "*Tip*\n"
                "Clear photos and short notes speed up approvals."
                "*COMMUNICATION*\n"
                " *Report Unavailability* - Notify supervisors\n"
                " When you receive messages, tap:\n"
                "  - *Acknowledge* - Confirm you've seen it\n"
                "  - *Reply* - Send a response\n\n"
                
                "*TIPS*\n"
                " Submit jobs with clear photos\n"
                " Keep your availability updated\n"
                " Respond to jobs promptly"
            )
        
        await message.answer(help_text, parse_mode="Markdown")


