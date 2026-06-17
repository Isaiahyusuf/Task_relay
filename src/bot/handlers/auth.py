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
from src.bot.i18n import variants as tv, msg as i18n_msg, get_recipient_lang
from src.bot.utils.translate import translate_text
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
            lang = getattr(user, "language", "en") or "en"
            keyboard = get_main_menu_keyboard(user.role, lang=lang)
            await message.answer(
                i18n_msg("welcome_back", lang=lang, name=message.from_user.first_name or "there", role=role_name),
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
            lang = getattr(user, "language", "en") or "en"
            keyboard = get_main_menu_keyboard(user.role, lang=lang)
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

@router.message(F.text.in_(tv("Help")))
async def btn_help(message: Message):
    await show_help(message)

@router.message(F.text.in_(tv("Delete My Account")))
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
    
    user_lang = getattr(user, "language", "en") or "en"
    await message.answer(
        i18n_msg("account_delete_confirm", lang=user_lang),
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
        
        user_lang = getattr(user, "language", "en") or "en"
        user.is_active = False
        await session.commit()
    
    await callback.message.edit_text(i18n_msg("account_deleted", lang=user_lang))
    await callback.answer()

@router.callback_query(F.data == "cancel_self_delete")
async def handle_cancel_self_delete(callback: CallbackQuery):
    user_lang = await get_recipient_lang(callback.from_user.id)
    await callback.message.edit_text(i18n_msg("account_delete_cancelled", lang=user_lang))
    await callback.answer()

@router.message(F.text.in_(tv("About")))
async def btn_about(message: Message):
    lang = "en"
    if async_session:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            u = result.scalar_one_or_none()
            if u:
                lang = getattr(u, "language", "en") or "en"

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
        "- IN-PROGRESS: Work has started\n"
        "- SUBMITTED: Sent for supervisor review\n"
        "- COMPLETED: Closed\n"
        "- CANCELLED or ARCHIVED: Closed out\n\n"
        "*Safety Flow*\n"
        "Subcontractors can submit Site Safety Checklists from the menu and choose the supervisor recipient. Managers and supervisors can review, filter, and export submissions.\n\n"
        "_TaskRelay - Operations first, chat-native workflow._"
    )
    if lang != "en":
        about_text = await translate_text(about_text, target_lang=lang, source_lang="en")
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
            await message.answer("Please use /start and register first.")
            return

        lang = getattr(user, "language", "en") or "en"

        if user.role == UserRole.SUPER_ADMIN:
            help_text = (
                "*GENERAL MANAGER HELP*\n\n"
                "*Daily Operations*\n"
                "- `Job History`, `Archive Jobs`, `View Archived`\n"
                "- `Safety Submissions`, `Filter Safety Submissions`, `Export Safety CSV`\n"
                "- `Send Message`\n\n"
                "*Access and People*\n"
                "- `All Access Codes` and `Manage Access Codes`\n"
                "- `Create Manager Code`, `Create Supervisor Code`, `Create Subcontractor Code`\n"
                "- `View Managers`, `View Supervisors`, `View Subcontractors`, `All Users`\n\n"
                "*Governance*\n"
                "- `Manage Roles`, `Manage Teams`, `Manage Regions`\n"
                "- `View By Teams`, `View Regions`\n\n"
                "*Tip*\n"
                "Use `Switch Role` only when testing role views."
            )
        elif user.role == UserRole.ADMIN:
            help_text = (
                "*MANAGER HELP*\n\n"
                "*Jobs*\n"
                "- `New Job` to dispatch quote or preset-price work\n"
                "- `Job History`, `Archive Jobs`, `View Archived`\n\n"
                "*Safety*\n"
                "- `Request Safety Checklist` when a checklist is required\n"
                "- `Safety Submissions`, `Filter Safety Submissions`, `Export Safety CSV`\n\n"
                "*Team and Access*\n"
                "- `Create Access Code` for supervisor and subcontractor onboarding\n"
                "- `Manage Access Codes`, `Manage Users`\n"
                "- `Manage Teams`, `Manage Regions`, `View By Teams`, `View Regions`\n\n"
                "*Communication*\n"
                "- `Send Message`, `Request Availability`, `Weekly Availability`\n\n"
                "*Tip*\n"
                "Use `Switch Role` only to check role-specific menu behavior."
            )
        elif user.role == UserRole.SUPERVISOR:
            help_text = (
                "*SUPERVISOR HELP*\n\n"
                "*Create and Track Work*\n"
                "- `New Job` to create quote or preset-price jobs\n"
                "- `My Jobs`, `Pending Jobs`, `Active Jobs`, `Submitted Jobs`\n"
                "- Review submissions and close jobs from the job actions\n\n"
                "*Safety*\n"
                "- `Request Safety Checklist` when needed\n"
                "- `Safety Submissions`, `Filter Safety Submissions`, `Export Safety CSV`\n\n"
                "*Access and Comms*\n"
                "- `Create Subcontractor Code`\n"
                "- `Manage Access Codes` for codes you are allowed to remove\n"
                "- `Send Message`\n\n"
                "*Tip*\n"
                "When reviewing submitted jobs, check photos and notes before closing."
            )
        else:
            help_text = (
                "*SUBCONTRACTOR HELP*\n\n"
                "*Jobs*\n"
                "- `Available Jobs` shows work assigned to you\n"
                "- `My Active Jobs` and `Start Work` for accepted jobs\n"
                "- `Submit Job` with clear photos and completion notes\n\n"
                "*Safety*\n"
                "- `Site Safety Checklist` can be submitted from menu\n"
                "- Choose a supervisor recipient in the checklist flow\n"
                "- `My Submissions` shows your checklist history\n\n"
                "*Availability and Contact*\n"
                "- Use `Available`, `Busy`, `Away` for live status\n"
                "- Update `My Availability` and use `Report Unavailability`\n"
                "- Use job updates and message replies when direction is needed\n\n"
                "*Tip*\n"
                "Fast approvals come from clear photos and short, accurate notes."
            )

        if lang != "en":
            help_text = await translate_text(help_text, target_lang=lang, source_lang="en")
        await message.answer(help_text, parse_mode="Markdown")


