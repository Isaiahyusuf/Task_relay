from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.orm import aliased
from src.bot.database import async_session, User, Job, AccessCode
from src.bot.database.models import UserRole, JobStatus, JobType, TeamType, Team, BroadcastMessage
from src.bot.services.jobs import JobService
from src.bot.services.archive import ArchiveService
from src.bot.services.access_codes import AccessCodeService
from src.bot.services.safety_checklist import SafetyChecklistService
from src.bot.utils.permissions import require_role
from src.bot.utils.roles import has_minimum_role, can_manage_role, creatable_roles, role_display_name
from src.bot.config import config
from src.bot.utils.keyboards import (
    get_role_selection_keyboard, get_job_list_keyboard, get_back_keyboard,
    get_user_list_keyboard, get_user_actions_keyboard, get_switch_role_keyboard,
    get_confirm_delete_keyboard, get_main_menu_keyboard, get_supervisor_job_actions_keyboard,
    get_confirm_job_delete_keyboard, get_team_selection_keyboard, get_message_target_keyboard,
    get_subcontractor_select_keyboard, get_availability_request_select_keyboard,
    get_weekly_availability_keyboard
)
from src.bot.database import WeeklyAvailability
import logging
import sqlalchemy
from src.bot.i18n import variants as tv, all_menu_variants, msg as i18n_msg, get_recipient_lang

logger = logging.getLogger(__name__)
router = Router()

class CreateCodeStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_role = State()
    waiting_for_team = State()
    waiting_for_region = State()
    confirming = State()

class SwitchRoleStates(StatesGroup):
    waiting_for_team = State()

class MessageStates(StatesGroup):
    selecting_target = State()
    selecting_users = State()
    composing_message = State()

class WeeklyAvailabilityNotes(StatesGroup):
    waiting_for_notes = State()


class AvailabilityRequestStates(StatesGroup):
    selecting_users = State()

@router.message(Command("history"))
@require_role(UserRole.ADMIN)
async def cmd_history(message: Message):
    await show_history(message)

@router.message(F.text.in_(tv("Job History")))
async def btn_history(message: Message):
    if not await check_admin(message):
        return
    await show_history(message)

async def check_admin(message: Message) -> bool:
    if not async_session:
        lang = await get_recipient_lang(message.from_user.id)
        await message.answer(i18n_msg("db_unavailable", lang=lang))
        return False
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        lang = (getattr(user, "language", "en") or "en") if user else "en"
        is_effective_admin = bool(
            user and (
                has_minimum_role(user.role, UserRole.ADMIN)
                or (user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE)
            )
        )
        if not is_effective_admin:
            await message.answer(i18n_msg("admin_no_permission", lang=lang))
            return False
    return True

async def check_super_admin(message: Message) -> bool:
    if not async_session:
        lang = await get_recipient_lang(message.from_user.id)
        await message.answer(i18n_msg("db_unavailable", lang=lang))
        return False
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        lang = (getattr(user, "language", "en") or "en") if user else "en"
        # A user with valid super admin identity can regain super admin capabilities
        # even if currently switched to a lower role.
        is_effective_super_admin = bool(
            user and (
                has_minimum_role(user.role, UserRole.SUPER_ADMIN)
                or (user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE)
            )
        )
        if not is_effective_super_admin:
            await message.answer(i18n_msg("sa_no_permission", lang=lang))
            return False
    return True

async def show_history(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    lang = await get_recipient_lang(message.from_user.id)
    jobs = await JobService.get_job_history(team_id=user.team_id if user else None, limit=50)
    
    if not jobs:
        await message.answer(i18n_msg("job_history_empty", lang=lang), parse_mode="Markdown")
        return
    
    status_counts = {}
    for job in jobs:
        status = job.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    summary = "\n".join([f"  {status.replace('_', ' ').title()}: {count}" for status, count in status_counts.items()])
    
    await message.answer(
        i18n_msg("job_history_title", lang=lang, count=len(jobs), summary=summary),
        reply_markup=get_job_list_keyboard(jobs, context="history"),
        parse_mode="Markdown"
    )

@router.message(Command("archive"))
@require_role(UserRole.ADMIN)
async def cmd_archive(message: Message):
    await archive_jobs(message)

@router.message(F.text.in_(tv("Archive Jobs")))
async def btn_archive(message: Message):
    if not await check_admin(message):
        return
    await archive_jobs(message)

async def archive_jobs(message: Message):
    lang = await get_recipient_lang(message.from_user.id)
    count = await ArchiveService.archive_old_jobs()
    
    if count > 0:
        await message.answer(i18n_msg("archive_complete", lang=lang, count=count), parse_mode="Markdown")
    else:
        await message.answer(i18n_msg("archive_empty", lang=lang), parse_mode="Markdown")

@router.message(Command("archived"))
@require_role(UserRole.ADMIN)
async def cmd_archived(message: Message):
    await show_archived(message)

@router.message(F.text.in_(tv("View Archived")))
async def btn_archived(message: Message):
    if not await check_admin(message):
        return
    await show_archived(message)

async def show_archived(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    lang = await get_recipient_lang(message.from_user.id)
    jobs = await ArchiveService.get_archived_jobs(team_id=user.team_id if user else None)
    
    if not jobs:
        await message.answer(i18n_msg("archived_jobs_empty", lang=lang), parse_mode="Markdown")
        return
    
    await message.answer(
        i18n_msg("archived_jobs_title", lang=lang, count=len(jobs)),
        reply_markup=get_job_list_keyboard(jobs, context="archived"),
        parse_mode="Markdown"
    )

@router.message(Command("createcode"))
@require_role(UserRole.ADMIN)
async def cmd_create_code(message: Message, state: FSMContext):
    parts = message.text.split()
    
    if len(parts) >= 3:
        code = parts[1]
        role_str = parts[2].lower()
        
        role_map = {
            "admin": UserRole.ADMIN,
            "supervisor": UserRole.SUPERVISOR,
            "subcontractor": UserRole.SUBCONTRACTOR
        }
        
        lang = await get_recipient_lang(message.from_user.id)
        if role_str not in role_map:
            await message.answer(i18n_msg("code_invalid_role", lang=lang))
            return
        
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()

        if not user:
            await message.answer(i18n_msg("user_not_found_err", lang=lang))
            return

        creator_role = user.role
        if user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE:
            creator_role = UserRole.SUPER_ADMIN

        target_role = role_map[role_str]
        if target_role not in creatable_roles(creator_role):
            await message.answer(i18n_msg("code_no_permission", lang=lang))
            return
        
        success = await AccessCodeService.create_access_code(
            code=code,
            role=target_role,
            team_id=user.team_id if user else None,
            created_by_id=user.id if user else None
        )
        
        if success:
            await message.answer(
                i18n_msg("code_created_simple", lang=lang, code=code, role=role_display_name(target_role)),
                parse_mode="Markdown"
            )
        else:
            await message.answer(i18n_msg("code_create_failed", lang=lang))
        return
    
    await start_code_creation(message, state)

@router.message(F.text.in_(tv("Create Access Code")))
async def btn_create_code(message: Message, state: FSMContext):
    if not await check_admin(message):
        return
    await start_code_creation(message, state)

@router.message(F.text.in_(tv("Create Admin Code")))
@router.message(F.text.in_(tv("Create Manager Code")))
async def btn_create_admin_code(message: Message, state: FSMContext):
    if not await check_super_admin(message):
        return
    await start_role_specific_code_creation(message, state, UserRole.ADMIN, "Manager")

@router.message(F.text.in_(tv("Create Supervisor Code")))
async def btn_create_supervisor_code(message: Message, state: FSMContext):
    if not await check_super_admin(message):
        return
    await start_role_specific_code_creation(message, state, UserRole.SUPERVISOR, "Supervisor")

@router.message(F.text.in_(tv("Create Subcontractor Code")))
async def btn_create_subcontractor_code(message: Message, state: FSMContext):
    # Check role hierarchy for subcontractor-code creation.
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user and user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE:
        effective_role = UserRole.SUPER_ADMIN
    else:
        effective_role = user.role if user else None
    if not user or not can_manage_role(effective_role, UserRole.SUBCONTRACTOR):
        lang = (getattr(user, "language", "en") or "en") if user else "en"
        await message.answer(i18n_msg("no_permission_create_sub_code", lang=lang))
        return
    
    await start_role_specific_code_creation(message, state, UserRole.SUBCONTRACTOR, "Subcontractor")

async def start_role_specific_code_creation(message: Message, state: FSMContext, role: UserRole, role_name: str):
    lang = await get_recipient_lang(message.from_user.id)
    await state.update_data(preset_role=role.value, preset_role_name=role_name, lang=lang)
    await message.answer(
        i18n_msg("code_enter_role_step", lang=lang, role_name=role_name),
        parse_mode="Markdown"
    )
    await state.set_state(CreateCodeStates.waiting_for_code)

async def start_code_creation(message: Message, state: FSMContext):
    lang = await get_recipient_lang(message.from_user.id)
    await state.update_data(lang=lang)
    await message.answer(
        i18n_msg("code_enter_step1", lang=lang),
        parse_mode="Markdown"
    )
    await state.set_state(CreateCodeStates.waiting_for_code)

MENU_BUTTON_TEXTS = all_menu_variants() | {"Back", "Cancel"}

@router.message(StateFilter(CreateCodeStates.waiting_for_code), ~F.text.in_(MENU_BUTTON_TEXTS))
async def process_code_input(message: Message, state: FSMContext):
    code = message.text.strip()
    
    data = await state.get_data()
    lang = data.get("lang") or await get_recipient_lang(message.from_user.id)

    if not code.isalnum():
        await message.answer(i18n_msg("code_must_be_alnum", lang=lang))
        return
    
    if len(code) < 4:
        await message.answer(i18n_msg("code_too_short", lang=lang))
        return
    
    forced_role = data.get("forced_role")
    preset_role = data.get("preset_role")
    preset_role_name = data.get("preset_role_name")
    
    if forced_role:
        # If role is forced (e.g. by supervisor), skip role selection step
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()
        
        success = await AccessCodeService.create_access_code(
            code=code,
            role=forced_role,
            team_id=user.team_id if user else None,
            created_by_id=user.id if user else None
        )
        
        if success:
            await message.answer(
                i18n_msg("code_created_full", lang=lang, code=code, role=forced_role.value.title(),
                         extra="Share this code privately with the intended subcontractor.\n"),
                parse_mode="Markdown"
            )
        else:
            await message.answer(i18n_msg("code_create_failed_exists", lang=lang))
        
        await state.clear()
        return
    
    if preset_role:
        # Role was pre-selected via specific button, go directly to team selection
        role_map = {
            "super_admin": UserRole.SUPER_ADMIN,
            "admin": UserRole.ADMIN,
            "supervisor": UserRole.SUPERVISOR,
            "subcontractor": UserRole.SUBCONTRACTOR
        }
        role = role_map.get(preset_role)
        await state.update_data(code=code, role=role, role_str=preset_role)
        
        await message.answer(
            i18n_msg("code_select_team", lang=lang, role_name=preset_role_name, code=code),
            reply_markup=get_team_selection_keyboard(for_code=True, lang=lang),
            parse_mode="Markdown"
        )
        await state.set_state(CreateCodeStates.waiting_for_team)
        return

    # Get creator's role to determine which roles they can create
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        creator = result.scalar_one_or_none()
        creator_role = creator.role.value if creator else "admin"
    
    await state.update_data(code=code, creator_role=creator_role)
    await message.answer(
        i18n_msg("code_select_role", lang=lang, code=code),
        reply_markup=get_role_selection_keyboard(creator_role=creator_role, lang=lang),
        parse_mode="Markdown"
    )
    await state.set_state(CreateCodeStates.waiting_for_role)

@router.callback_query(F.data.startswith("role:"), StateFilter(CreateCodeStates.waiting_for_role))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    role_str = callback.data.split(":")[1]
    data = await state.get_data()
    
    role_map = {
        "super_admin": UserRole.SUPER_ADMIN,
        "admin": UserRole.ADMIN,
        "supervisor": UserRole.SUPERVISOR,
        "subcontractor": UserRole.SUBCONTRACTOR
    }
    
    selected_role = role_map.get(role_str)
    if not selected_role:
        await callback.answer("Invalid role", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        creator = result.scalar_one_or_none()

    if not creator:
        lang = data.get("lang") or await get_recipient_lang(callback.from_user.id)
        await callback.answer(i18n_msg("user_not_found_err", lang=lang), show_alert=True)
        return

    creator_role = creator.role
    if creator.super_admin_code and creator.super_admin_code == config.SUPER_ADMIN_CODE:
        creator_role = UserRole.SUPER_ADMIN

    if selected_role not in creatable_roles(creator_role):
        lang = data.get("lang") or await get_recipient_lang(callback.from_user.id)
        await callback.answer(i18n_msg("code_no_permission", lang=lang), show_alert=True)
        return

    await state.update_data(role=selected_role, role_str=role_str)
    
    # Ask for team assignment for admin, supervisor, and subcontractor
    if role_str in ["admin", "supervisor", "subcontractor"]:
        from src.bot.utils.keyboards import get_team_selection_keyboard
        role_label = role_str.title()
        lang = data.get("lang") or await get_recipient_lang(callback.from_user.id)
        await callback.message.edit_text(
            i18n_msg("select_team_for_role", lang=lang, role_label=role_label),
            reply_markup=get_team_selection_keyboard(for_code=True, lang=lang),
            parse_mode="Markdown"
        )
        await state.set_state(CreateCodeStates.waiting_for_team)
    else:
        # For super_admin, no team assignment needed
        await create_code_with_team(callback, state, team_type=None)
    
    await callback.answer()

@router.callback_query(F.data.startswith("code_team:"), StateFilter(CreateCodeStates.waiting_for_team))
async def process_team_selection(callback: CallbackQuery, state: FSMContext):
    team_type = callback.data.split(":")[1]
    await create_code_with_team(callback, state, team_type=team_type)
    await callback.answer()

async def create_code_with_team(callback: CallbackQuery, state: FSMContext, team_type: str = None):
    from src.bot.database.models import TeamType, Team, Region
    
    data = await state.get_data()
    code = data.get('code')
    role = data.get('role')
    role_str = data.get('role_str')
    
    team_id = None
    team_name = None
    
    if team_type:
        async with async_session() as session:
            team_type_enum = TeamType.NORTHWEST if team_type == "northwest" else TeamType.SOUTHEAST
            result = await session.execute(
                select(Team).where(Team.team_type == team_type_enum)
            )
            team = result.scalar_one_or_none()
            if team:
                team_id = team.id
                team_name = team.name
    
    await state.update_data(team_id=team_id, team_name=team_name)
    
    # Check if there are any regions available
    async with async_session() as session:
        region_result = await session.execute(
            select(Region).where(Region.is_active == True).order_by(Region.name)
        )
        regions = list(region_result.scalars().all())
    
    if regions:
        lang = data.get("lang") or await get_recipient_lang(callback.from_user.id)
        # Show region selection
        keyboard = InlineKeyboardBuilder()
        for region in regions:
            keyboard.row(InlineKeyboardButton(
                text=f" {region.name}",
                callback_data=f"code_region:{region.id}"
            ))
        keyboard.row(InlineKeyboardButton(text=" Skip (No Region)", callback_data="code_region:skip"))
        keyboard.row(InlineKeyboardButton(text=i18n_msg("btn_cancel", lang=lang), callback_data="cancel_code"))
        
        await callback.message.edit_text(
            i18n_msg("code_select_region", lang=lang, code=code, role=role_str.title(), team=team_name or "None"),
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await state.set_state(CreateCodeStates.waiting_for_region)
    else:
        # No regions, create code immediately
        await finalize_code_creation(callback, state, region_id=None)

@router.callback_query(F.data.startswith("code_region:"), StateFilter(CreateCodeStates.waiting_for_region))
async def process_region_selection_for_code(callback: CallbackQuery, state: FSMContext):
    region_value = callback.data.split(":")[1]
    region_id = None if region_value == "skip" else int(region_value)
    await finalize_code_creation(callback, state, region_id=region_id)
    await callback.answer()

async def finalize_code_creation(callback: CallbackQuery, state: FSMContext, region_id: int = None):
    from src.bot.database.models import Region
    
    data = await state.get_data()
    code = data.get('code')
    role = data.get('role')
    role_str = data.get('role_str')
    team_id = data.get('team_id')
    team_name = data.get('team_name')
    
    region_name = None
    creator_user_id = None
    if region_id:
        async with async_session() as session:
            result = await session.execute(
                select(Region).where(Region.id == region_id)
            )
            region = result.scalar_one_or_none()
            if region:
                region_name = region.name
            creator_result = await session.execute(
                select(User).where(User.telegram_id == callback.from_user.id)
            )
            creator = creator_result.scalar_one_or_none()
            if creator:
                creator_user_id = creator.id
    else:
        async with async_session() as session:
            creator_result = await session.execute(
                select(User).where(User.telegram_id == callback.from_user.id)
            )
            creator = creator_result.scalar_one_or_none()
            if creator:
                creator_user_id = creator.id
    
    success = await AccessCodeService.create_access_code(
        code=code,
        role=role,
        team_id=team_id,
        region_id=region_id,
        created_by_id=creator_user_id
    )
    
    lang = data.get("lang") or await get_recipient_lang(callback.from_user.id)
    if success:
        team_info = f"Team: {team_name}\n" if team_name else ""
        region_info = f"Region: {region_name}\n" if region_name else ""
        extra = f"{team_info}{region_info}"
        await callback.message.edit_text(
            i18n_msg("code_created_full", lang=lang, code=code, role=role_str.title(), extra=extra),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(i18n_msg("code_create_failed_exists", lang=lang))
    
    await state.clear()

@router.callback_query(F.data == "cancel_code")
async def cancel_code_from_team(callback: CallbackQuery, state: FSMContext):
    lang = await get_recipient_lang(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(i18n_msg("code_cancelled", lang=lang))
    await callback.answer()

@router.callback_query(F.data == "code_cancel")
async def cancel_code_creation(callback: CallbackQuery, state: FSMContext):
    lang = await get_recipient_lang(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(i18n_msg("code_cancelled", lang=lang))
    await callback.answer()

@router.callback_query(F.data.startswith("page:history:"))
async def handle_history_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[2])
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    jobs = await JobService.get_job_history(team_id=user.team_id if user else None, limit=50)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_job_list_keyboard(jobs, page=page, context="history")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("page:archived:"))
async def handle_archived_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[2])
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    jobs = await ArchiveService.get_archived_jobs(team_id=user.team_id if user else None)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_job_list_keyboard(jobs, page=page, context="archived")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_job:history:"))
async def view_job_details_history(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[2])
    await show_job_details(callback, job_id, "history")

@router.callback_query(F.data.startswith("view_job:archived:"))
async def view_job_details_archived(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[2])
    await show_job_details(callback, job_id, "archived")

async def show_job_details(callback: CallbackQuery, job_id: int, context: str):
    if not async_session:
        await callback.answer("Database error", show_alert=True)
        return
    
    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    status_text = {
        JobStatus.CREATED: "Created",
        JobStatus.SENT: "Sent",
        JobStatus.ACCEPTED: "Accepted",
        JobStatus.IN_PROGRESS: "In Progress",
        JobStatus.SUBMITTED: "Submitted",
        JobStatus.COMPLETED: "Completed",
        JobStatus.CANCELLED: "Cancelled",
        JobStatus.ARCHIVED: "Archived"
    }.get(job.status, "Unknown")
    
    type_text = "Quote" if job.job_type == JobType.QUOTE else "Preset Price"
    
    details = (
        f"*Job #{job.id}*\n\n"
        f"*Title:* {job.title}\n"
        f"*Type:* {type_text}\n"
        f"*Status:* {status_text}\n"
    )
    
    if job.description:
        details += f"*Description:* {job.description}\n"
    if job.address:
        details += f"*Address:* {job.address}\n"
    if job.preset_price:
        details += f"*Price:* {job.preset_price}\n"
    if job.decline_reason:
        details += f"*Decline Reason:* {job.decline_reason}\n"
    
    details += f"\n*Created:* {job.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    await callback.message.edit_text(
        details,
        reply_markup=get_supervisor_job_actions_keyboard(job.id, job.status.value, job.job_type.value, is_admin=True),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_delete_job:"))
async def handle_admin_delete_job(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    lang = await get_recipient_lang(callback.from_user.id)
    
    if not await check_admin(callback.message):
        await callback.answer("Not authorized", show_alert=True)
        return

    await callback.message.edit_text(
        i18n_msg("delete_job_confirm_msg", lang=lang, job_id=job_id),
        reply_markup=get_confirm_job_delete_keyboard(job_id, lang=lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_job_delete:"))
async def handle_confirm_job_delete(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        # Check admin or super admin
        admin_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        admin = admin_result.scalar_one_or_none()
        if not admin or admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            await callback.answer("Not authorized", show_alert=True)
            return

        # Delete quotes first to maintain integrity
        from src.bot.database import Quote
        await session.execute(
            sqlalchemy.delete(Quote).where(Quote.job_id == job_id)
        )
        
        # Delete job
        await session.execute(
            sqlalchemy.delete(Job).where(Job.id == job_id)
        )
        await session.commit()

    lang = await get_recipient_lang(callback.from_user.id)
    await callback.message.edit_text(
        i18n_msg("job_deleted_msg", lang=lang, job_id=job_id),
        reply_markup=get_back_keyboard("back:history", lang=lang)
    )
    await callback.answer()

@router.callback_query(F.data == "back:history")
async def back_to_history(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    lang = await get_recipient_lang(callback.from_user.id)
    jobs = await JobService.get_job_history(team_id=user.team_id if user else None, limit=50)
    
    status_counts = {}
    for job in jobs:
        status = job.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    summary = "\n".join([f"  {status.replace('_', ' ').title()}: {count}" for status, count in status_counts.items()])
    
    await callback.message.edit_text(
        i18n_msg("job_history_title", lang=lang, count=len(jobs), summary=summary),
        reply_markup=get_job_list_keyboard(jobs, context="history"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back:archived")
async def back_to_archived(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    lang = await get_recipient_lang(callback.from_user.id)
    jobs = await ArchiveService.get_archived_jobs(team_id=user.team_id if user else None)
    
    await callback.message.edit_text(
        i18n_msg("archived_jobs_title", lang=lang, count=len(jobs)),
        reply_markup=get_job_list_keyboard(jobs, context="archived"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(F.text.in_(tv("Manage Users")))
async def btn_manage_users(message: Message):
    if not await check_admin(message):
        return
    await show_user_list(message)

def get_effective_role(user: User) -> UserRole:
    if user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE:
        return UserRole.SUPER_ADMIN
    return user.role


def can_delete_access_code(actor: User, code: AccessCode, creator: User | None) -> bool:
    actor_role = get_effective_role(actor)

    if actor_role == UserRole.SUPER_ADMIN:
        return True

    if actor_role == UserRole.ADMIN:
        if code.created_by_id == actor.id:
            return True
        if creator and creator.role == UserRole.SUPERVISOR:
            if actor.team_id is None:
                return True
            return code.team_id == actor.team_id
        return False

    if actor_role == UserRole.SUPERVISOR:
        return code.created_by_id == actor.id

    return False


def creator_display_name(creator: User | None) -> str:
    if not creator:
        return "Unknown"
    return creator.first_name or creator.username or f"User {creator.telegram_id}"


async def show_all_access_codes(message: Message):
    await show_manage_access_codes(message, telegram_user_id=message.from_user.id)


async def show_manage_access_codes(message: Message, telegram_user_id: int, edit: bool = False):
    creator_alias = aliased(User)

    async with async_session() as session:
        actor_result = await session.execute(
            select(User).where(User.telegram_id == telegram_user_id)
        )
        actor = actor_result.scalar_one_or_none()

        if not actor:
            if edit:
                await message.edit_text("User record not found.")
            else:
                await message.answer("User record not found.")
            return

        role = get_effective_role(actor)
        if role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPERVISOR]:
            if edit:
                await message.edit_text("You don't have permission to manage access codes.")
            else:
                await message.answer("You don't have permission to manage access codes.")
            return

        result = await session.execute(
            select(AccessCode, creator_alias)
            .outerjoin(creator_alias, AccessCode.created_by_id == creator_alias.id)
            .where(AccessCode.is_active == True)
            .order_by(AccessCode.role, AccessCode.code)
        )
        all_rows = list(result.all())

    visible_rows = [row for row in all_rows if can_delete_access_code(actor, row[0], row[1])]

    if not visible_rows:
        text = (
            "*Manage Access Codes*\n\n"
            "No access codes are available for your role."
        )
        if edit:
            await message.edit_text(text, parse_mode="Markdown")
        else:
            await message.answer(text, parse_mode="Markdown")
        return

    keyboard = InlineKeyboardBuilder()
    lines = []

    max_visible = 20
    for code, creator in visible_rows[:max_visible]:
        uses_text = f"{code.current_uses}/{code.max_uses}" if code.max_uses else str(code.current_uses)
        lines.append(
            f"- `{code.code}` | {role_display_name(code.role)} | Uses: {uses_text} | Created by: {creator_display_name(creator)}"
        )
        keyboard.row(
            InlineKeyboardButton(
                text=f"Delete {code.code}",
                callback_data=f"delete_code:{code.id}"
            )
        )

    if len(visible_rows) > max_visible:
        lines.append(f"\nShowing first {max_visible} of {len(visible_rows)} codes.")

    text = (
        f"*Manage Access Codes* ({len(visible_rows)})\n\n"
        + "\n".join(lines)
    )

    if edit:
        await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("delete_code:"))
async def delete_access_code(callback: CallbackQuery):
    code_id = int(callback.data.split(":")[1])
    creator_alias = aliased(User)

    async with async_session() as session:
        actor_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        actor = actor_result.scalar_one_or_none()
        if not actor:
            await callback.answer("User not found.", show_alert=True)
            return

        code_result = await session.execute(
            select(AccessCode, creator_alias)
            .outerjoin(creator_alias, AccessCode.created_by_id == creator_alias.id)
            .where(AccessCode.id == code_id)
        )
        row = code_result.one_or_none()
        if not row:
            await callback.answer("Code not found.", show_alert=True)
            return

        code, creator = row
        if not code.is_active:
            await callback.answer("Code already deleted.", show_alert=True)
            return

        if not can_delete_access_code(actor, code, creator):
            await callback.answer("You cannot delete this code.", show_alert=True)
            return

        code.is_active = False
        await session.commit()

    await callback.answer("Access code deleted.")
    await show_manage_access_codes(callback.message, telegram_user_id=callback.from_user.id, edit=True)


@router.message(F.text.in_(tv("Manage Access Codes")))
async def btn_manage_access_codes(message: Message, state: FSMContext):
    await state.clear()
    await show_manage_access_codes(message, telegram_user_id=message.from_user.id)

@router.message(F.text.in_(tv("View By Teams")))
async def btn_view_by_teams(message: Message, state: FSMContext):
    await state.clear()
    
    # Check if admin or super admin
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    if not user or user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        await message.answer("Only admins can view team members.")
        return
    
    # Super admins see all teams, admins only see their own team.
    is_super_admin = get_effective_role(user) == UserRole.SUPER_ADMIN
    await show_team_hierarchy(message, user_team_id=user.team_id if not is_super_admin else None, is_super_admin=is_super_admin)

async def show_team_hierarchy(message: Message, user_team_id: int = None, is_super_admin: bool = False):
    from src.bot.database.models import Team, TeamType
    
    async with async_session() as session:
        # Get teams based on access level
        if is_super_admin or user_team_id is None:
            # Super admin sees all teams
            teams_result = await session.execute(select(Team).order_by(Team.name))
        else:
            # Admin only sees their own team
            teams_result = await session.execute(
                select(Team).where(Team.id == user_team_id)
            )
        teams = list(teams_result.scalars().all())
        
        # Get users - super admin sees all, admin sees their team only
        if is_super_admin:
            users_result = await session.execute(
                select(User).where(User.is_active == True).order_by(User.first_name)
            )
        else:
            users_result = await session.execute(
                select(User).where(
                    User.is_active == True,
                    User.team_id == user_team_id
                ).order_by(User.first_name)
            )
        all_users = list(users_result.scalars().all())
    
    title = "* All Teams Hierarchy*" if is_super_admin else "* My Team Hierarchy*"
    text = f"{title}\n\n"
    
    # Group users by team
    team_users = {}
    unassigned = []
    
    for user in all_users:
        if user.team_id:
            if user.team_id not in team_users:
                team_users[user.team_id] = []
            team_users[user.team_id].append(user)
        else:
            unassigned.append(user)
    
    # Display each team
    for team in teams:
        text += f"*{team.name}*\n"
        
        users_in_team = team_users.get(team.id, [])
        
        if users_in_team:
            # Group by role within team
            role_order = [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.SUBCONTRACTOR]
            role_emojis = {
                UserRole.ADMIN: "",
                UserRole.SUPERVISOR: "",
                UserRole.SUBCONTRACTOR: ""
            }
            
            for role in role_order:
                role_users = [u for u in users_in_team if u.role == role]
                if role_users:
                    text += f"  {role_emojis.get(role, '')} *{role.value.replace('_', ' ').title()}s:*\n"
                    for u in role_users:
                        name = u.first_name or "Unknown"
                        text += f"     {name}\n"
        else:
            text += "  _No members_\n"
        
        text += "\n"
    
    # Show unassigned users (Super Admins and others without team) - only for super admins
    if is_super_admin and unassigned:
        text += " *General Managers / Unassigned*\n"
        for u in unassigned:
            role_emoji = "" if u.role == UserRole.SUPER_ADMIN else ""
            name = u.first_name or "Unknown"
            text += f"  {role_emoji} {name} ({u.role.value.replace('_', ' ').title()})\n"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text.in_(tv("View Admins")))
@router.message(F.text.in_(tv("View Managers")))
async def btn_view_admins(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_users_by_role(message, UserRole.ADMIN, "Managers")

@router.message(F.text.in_(tv("View Supervisors")))
async def btn_view_supervisors(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_users_by_role(message, UserRole.SUPERVISOR, "Supervisors")

@router.message(F.text.in_(tv("View Subcontractors")))
async def btn_view_subcontractors(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_users_by_role(message, UserRole.SUBCONTRACTOR, "Subcontractors")

@router.message(F.text.in_(tv("All Access Codes")))
async def btn_all_access_codes_v2(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_all_access_codes(message)

@router.message(F.text.in_(tv("All Users")))
async def btn_all_users_v2(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_user_list(message, is_super_admin=True)

async def show_users_by_role(message: Message, role: UserRole, role_name: str):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_active == True, User.role == role).order_by(User.first_name)
        )
        users = list(result.scalars().all())
    
    lang = await get_recipient_lang(message.from_user.id)
    if not users:
        await message.answer(
            i18n_msg("users_by_role_none", lang=lang, role_name=role_name, role_name_lower=role_name.lower()),
            parse_mode="Markdown"
        )
        return
    
    if role == UserRole.SUBCONTRACTOR:
        text = i18n_msg("users_by_role_title", lang=lang, role_name=role_name, count=len(users)) + "\n"
        for u in users:
            name = u.first_name or "Unknown"
            text += f" {name}\n"
        await message.answer(
            text,
            reply_markup=get_user_list_keyboard(users, is_super_admin=True),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            i18n_msg("users_by_role_title", lang=lang, role_name=role_name, count=len(users)),
            reply_markup=get_user_list_keyboard(users, is_super_admin=True),
            parse_mode="Markdown"
        )

@router.message(F.text.in_(tv("Switch Role")))
async def btn_switch_role_super_admin(message: Message, state: FSMContext):
    await state.clear()
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    if not user:
        lang = "en"
        await message.answer(i18n_msg("user_not_found_err", lang=lang))
        return
    
    lang = await get_recipient_lang(message.from_user.id)
    # Check if super admin or has super admin code
    if user.role == UserRole.SUPER_ADMIN:
        from src.bot.utils.keyboards import get_super_admin_switch_role_keyboard
        await message.answer(
            i18n_msg("switch_role_sa_prompt", lang=lang),
            reply_markup=get_super_admin_switch_role_keyboard(lang=lang),
            parse_mode="Markdown"
        )
    elif user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE:
        # User was a super admin, show return option
        await message.answer(
            i18n_msg("switch_role_return_prompt", lang=lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=i18n_msg("btn_return_to_gm", lang=lang), callback_data="sa_switch:super_admin")],
                [InlineKeyboardButton(text=i18n_msg("btn_cancel", lang=lang), callback_data="back:main")]
            ]),
            parse_mode="Markdown"
        )
    elif user.role == UserRole.ADMIN:
        await message.answer(
            i18n_msg("switch_role_admin_prompt", lang=lang),
            reply_markup=get_switch_role_keyboard(lang=lang),
            parse_mode="Markdown"
        )
    else:
        await message.answer(i18n_msg("switch_role_no_permission", lang=lang))

@router.callback_query(F.data.startswith("sa_switch:"))
async def handle_super_admin_switch(callback: CallbackQuery):
    role_str = callback.data.split(":")[1]
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("User not found", show_alert=True)
            return
        
        from src.bot.config import config
        
        lang = await get_recipient_lang(callback.from_user.id)
        if role_str == "super_admin":
            # Return to super admin
            if user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE:
                user.role = UserRole.SUPER_ADMIN
                await session.commit()
                
                await callback.message.edit_text(
                    i18n_msg("welcome_back_gm", lang=lang),
                    parse_mode="Markdown"
                )
                keyboard = get_main_menu_keyboard(UserRole.SUPER_ADMIN)
                await callback.message.answer(
                    i18n_msg("use_menu_below", lang=lang),
                    reply_markup=keyboard
                )
            else:
                await callback.answer(i18n_msg("cannot_return_gm", lang=lang), show_alert=True)
        else:
            # Switch to another role
            if user.role != UserRole.SUPER_ADMIN and not user.super_admin_code:
                await callback.answer(i18n_msg("not_authorized", lang=lang), show_alert=True)
                return
            
            role_map = {
                "admin": UserRole.ADMIN,
                "supervisor": UserRole.SUPERVISOR,
                "subcontractor": UserRole.SUBCONTRACTOR
            }
            
            new_role = role_map.get(role_str)
            if not new_role:
                await callback.answer("Invalid role", show_alert=True)
                return
            
            # For subcontractor, ask for team selection first
            if role_str == "subcontractor":
                
                # Store the pending role change and ask for team
                kb = InlineKeyboardBuilder()
                kb.button(text=i18n_msg("btn_team_northwest", lang=lang), callback_data="switch_team:northwest")
                kb.button(text=i18n_msg("btn_team_southeast", lang=lang), callback_data="switch_team:southeast")
                kb.adjust(1)
                
                await callback.message.edit_text(
                    i18n_msg("select_team_sub_prompt", lang=lang),
                    reply_markup=kb.as_markup(),
                    parse_mode="Markdown"
                )
                await callback.answer()
                return
            
            user.role = new_role
            await session.commit()
            
            await callback.message.edit_text(
                i18n_msg("role_changed_msg", lang=lang, role=role_str.title()),
                parse_mode="Markdown"
            )
            keyboard = get_main_menu_keyboard(new_role)
            await callback.message.answer(
                i18n_msg("use_menu_below", lang=lang),
                reply_markup=keyboard
            )
    
    await callback.answer()

@router.callback_query(F.data == "back:sa_menu")
async def back_to_super_admin_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data.startswith("switch_team:"))
async def handle_switch_team_selection(callback: CallbackQuery):
    team_type_str = callback.data.split(":")[1]
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("User not found", show_alert=True)
            return
        
        # Get the team
        team_type = TeamType.NORTHWEST if team_type_str == "northwest" else TeamType.SOUTHEAST
        team_result = await session.execute(
            select(Team).where(Team.team_type == team_type)
        )
        team = team_result.scalar_one_or_none()
        
        if not team:
            await callback.answer("Team not found", show_alert=True)
            return
        
        # Update user role and team
        user.role = UserRole.SUBCONTRACTOR
        user.team_id = team.id
        await session.commit()
        
        lang = await get_recipient_lang(callback.from_user.id)
        await callback.message.edit_text(
            i18n_msg("role_changed_with_team_msg", lang=lang, team=team.name),
            parse_mode="Markdown"
        )
        keyboard = get_main_menu_keyboard(UserRole.SUBCONTRACTOR)
        await callback.message.answer(
            i18n_msg("use_menu_below", lang=lang),
            reply_markup=keyboard
        )
    
    await callback.answer()

@router.message(F.text.in_(tv("Return to Super Admin")))
@router.message(F.text.in_(tv("Return to General Manager")))
async def btn_return_to_super_admin(message: Message, state: FSMContext):
    await state.clear()
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("User not found.")
            return
        
        from src.bot.config import config
        
        lang = await get_recipient_lang(message.from_user.id)
        if user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE:
            user.role = UserRole.SUPER_ADMIN
            await session.commit()
            
            keyboard = get_main_menu_keyboard(UserRole.SUPER_ADMIN)
            await message.answer(
                i18n_msg("welcome_back_gm", lang=lang),
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await message.answer(i18n_msg("return_gm_failed", lang=lang))

async def show_user_list(message: Message, is_super_admin: bool = False):
    async with async_session() as session:
        admin_result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        admin = admin_result.scalar_one_or_none()
        
        result = await session.execute(
            select(User).where(User.is_active == True).order_by(User.role, User.first_name)
        )
        users = list(result.scalars().all())
    
    lang = await get_recipient_lang(message.from_user.id)
    if not users:
        await message.answer(i18n_msg("no_users_found", lang=lang))
        return
    
    title_key = "manage_users_sa_title" if is_super_admin else "manage_users_admin_title"
    await message.answer(
        i18n_msg(title_key, lang=lang, count=len(users)),
        reply_markup=get_user_list_keyboard(users, is_super_admin=is_super_admin),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("manage_user:"))
async def handle_manage_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        admin_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        admin = admin_result.scalar_one_or_none()
        
        if not admin or admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            await callback.answer("Not authorized", show_alert=True)
            return
        
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("User not found", show_alert=True)
            return
        
        # Extract all needed data within the session
        is_self = user.telegram_id == callback.from_user.id
        role_text = role_display_name(user.role)
        name = user.first_name or user.username or f"User {user.telegram_id}"
        username = user.username or 'N/A'
        is_active = user.is_active
        created_date = user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'
        user_role = user.role
        stored_user_id = user.id
    
    safety_text = ""
    if user_role == UserRole.SUBCONTRACTOR:
        # General Manager can see this subcontractor's submitted checklist history.
        if admin and admin.role == UserRole.SUPER_ADMIN:
            checklists = await SafetyChecklistService.list_subcontractor_checklists(stored_user_id, limit=5)
            if checklists:
                safety_text = "\n*Recent Safety Checklists:*\n"
                for c in checklists:
                    safety_text += (
                        f"- #{c.id} | {c.status} | {c.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    )
            else:
                safety_text = "\n*Recent Safety Checklists:* None\n"
    
    # Handle username display - don't show @ for N/A
    username_display = f"@{username}" if username and username != 'N/A' else "Not set"
    
    lang = await get_recipient_lang(callback.from_user.id)
    status_str = i18n_msg("user_status_active", lang=lang) if is_active else i18n_msg("user_status_inactive", lang=lang)
    self_note = i18n_msg("user_self_note", lang=lang) if is_self else ""
    await callback.message.edit_text(
        i18n_msg("user_details_text", lang=lang,
                 name=name, username=username_display, role=role_text,
                 status=status_str, joined=created_date, safety=safety_text, self_note=self_note),
        reply_markup=get_user_actions_keyboard(user_id, is_self, lang=lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_user:"))
async def handle_delete_user_request(callback: CallbackQuery):
    parts = callback.data.split(":")
    user_id = int(parts[1])
    delete_type = parts[2]
    
    async with async_session() as session:
        admin_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        admin = admin_result.scalar_one_or_none()
        
        if not admin or admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            await callback.answer("Not authorized", show_alert=True)
            return
        
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    
    if not user:
        await callback.answer("User not found", show_alert=True)
        return
    
    # Only super admins can delete admins
    if user.role == UserRole.ADMIN and delete_type == "other" and admin.role != UserRole.SUPER_ADMIN:
        await callback.answer("Only Super Admins can delete other admins", show_alert=True)
        return
    
    name = user.first_name or user.username or f"User {user.telegram_id}"
    
    lang = await get_recipient_lang(callback.from_user.id)
    if delete_type == "self":
        warning = i18n_msg("delete_user_self_confirm", lang=lang)
    else:
        warning = i18n_msg("delete_user_other_confirm", lang=lang, name=name)
    
    await callback.message.edit_text(
        warning,
        reply_markup=get_confirm_delete_keyboard(user_id, delete_type, lang=lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete:"))
async def handle_confirm_delete(callback: CallbackQuery):
    parts = callback.data.split(":")
    user_id = int(parts[1])
    delete_type = parts[2]
    
    async with async_session() as session:
        admin_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        admin = admin_result.scalar_one_or_none()
        
        if not admin or admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            await callback.answer("Not authorized", show_alert=True)
            return
        
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("User not found", show_alert=True)
            return
        
        name = user.first_name or user.username or f"User {user.telegram_id}"
        is_self = user.telegram_id == callback.from_user.id
        
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
    
    lang = await get_recipient_lang(callback.from_user.id)
    if is_self:
        await callback.message.edit_text(i18n_msg("account_deleted_self", lang=lang))
    else:
        await callback.message.edit_text(
            i18n_msg("user_deleted_other", lang=lang, name=name),
            parse_mode="Markdown"
        )
    
    await callback.answer()

@router.callback_query(F.data == "back:users")
async def back_to_users(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_active == True).order_by(User.role, User.first_name)
        )
        users = list(result.scalars().all())
    
    lang = await get_recipient_lang(callback.from_user.id)
    await callback.message.edit_text(
        i18n_msg("back_to_users_title", lang=lang, count=len(users)),
        reply_markup=get_user_list_keyboard(users),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_regions")
async def back_to_regions(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Region).where(Region.is_active == True).order_by(Region.name)
        )
        regions = list(result.scalars().all())

    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=" Create New Region", callback_data="create_region"))
    for region in regions:
        keyboard.row(InlineKeyboardButton(text=f" {region.name}", callback_data=f"view_region:{region.id}"))

    await callback.message.edit_text(
        "* Manage Regions*\n\n"
        f"You have {len(regions)} region(s).\n\n"
        "Regions let you organize users and jobs by geographic area.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_teams")
async def back_to_teams(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(Team).order_by(Team.name))
        teams = list(result.scalars().all())

    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=" Create New Team", callback_data="create_team"))
    for team in teams:
        keyboard.row(InlineKeyboardButton(text=f" {team.name}", callback_data=f"view_team:{team.id}"))

    await callback.message.edit_text(
        "* Manage Teams*\n\n"
        f"You have {len(teams)} team(s).\n\n"
        "Teams help organize subcontractors into groups.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back:admin_menu")
async def back_to_admin_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data.startswith("page:users:"))
async def handle_users_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[2])
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_active == True).order_by(User.role, User.first_name)
        )
        users = list(result.scalars().all())
    
    await callback.message.edit_reply_markup(
        reply_markup=get_user_list_keyboard(users, page=page)
    )
    await callback.answer()

@router.message(F.text.in_(tv("Switch Role")))
async def btn_switch_role(message: Message):
    if not await check_admin(message):
        return
    
    await message.answer(
        "*Switch Your Role*\n\n"
        "You are currently an Admin.\n\n"
        " *Warning:* Switching roles will change your access level.\n"
        "You can ask another admin to switch you back later.\n\n"
        "Select your new role:",
        reply_markup=get_switch_role_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("switch_role:"))
async def handle_switch_role(callback: CallbackQuery):
    new_role_str = callback.data.split(":")[1]
    
    role_map = {
        "supervisor": UserRole.SUPERVISOR,
        "subcontractor": UserRole.SUBCONTRACTOR
    }
    
    new_role = role_map.get(new_role_str)
    if not new_role:
        await callback.answer("Invalid role", show_alert=True)
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user or user.role != UserRole.ADMIN:
            await callback.answer("Not authorized", show_alert=True)
            return
        
        if user.access_code_id:
            from src.bot.database import AccessCode
            code_result = await session.execute(
                select(AccessCode).where(AccessCode.id == user.access_code_id)
            )
            access_code = code_result.scalar_one_or_none()
            if access_code and access_code.current_uses > 0:
                access_code.current_uses -= 1
        
        user.role = new_role
        user.access_code_id = None
        await session.commit()
    
    keyboard = get_main_menu_keyboard(new_role)
    
    await callback.message.edit_text(
        f"*Role Changed!*\n\n"
        f"You are now a *{new_role_str.title()}*.\n\n"
        f"Your admin access code has been freed up for reuse.",
        parse_mode="Markdown"
    )
    
    await callback.message.answer(
        f"Welcome to your new role as {new_role_str.title()}!\n\n"
        "Use the menu below:",
        reply_markup=keyboard
    )
    await callback.answer()

# ============= ADMIN/SUPER ADMIN JOB CREATION =============

@router.message(F.text.in_(tv("New Job")))
async def btn_admin_new_job(message: Message, state: FSMContext):
    """Allow admins to create jobs (shared with supervisor flow)"""
    if not async_session:
        lang = await get_recipient_lang(message.from_user.id)
        await message.answer(i18n_msg("db_unavailable", lang=lang))
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
            lang = (getattr(user, "language", "en") or "en") if user else "en"
            await message.answer(i18n_msg("no_permission_create_job", lang=lang))
            return
    
    # Import and use supervisor's job creation flow
    from src.bot.handlers.supervisor import start_new_job
    await start_new_job(message, state)

# ============= ADMIN MESSAGING =============

@router.message(F.text.in_(tv("Send Message")))
async def btn_send_message(message: Message, state: FSMContext):
    """Start the messaging flow for admins and supervisors"""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SUPERVISOR]:
            lang = (getattr(user, "language", "en") or "en") if user else "en"
            await message.answer(i18n_msg("no_permission_send_msg", lang=lang))
            return
    
    lang = await get_recipient_lang(message.from_user.id)
    await message.answer(
        i18n_msg("send_message_prompt", lang=lang),
        reply_markup=get_message_target_keyboard(user.role if user else None, lang=lang),
        parse_mode="Markdown"
    )
    await state.set_state(MessageStates.selecting_target)

@router.callback_query(F.data == "msg_cancel")
async def cancel_message(callback: CallbackQuery, state: FSMContext):
    lang = await get_recipient_lang(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(i18n_msg("message_cancelled_msg", lang=lang))
    await callback.answer()

@router.callback_query(F.data.startswith("msg_target:"), StateFilter(MessageStates.selecting_target))
async def process_message_target(callback: CallbackQuery, state: FSMContext):
    target = callback.data.split(":")[1]
    lang = await get_recipient_lang(callback.from_user.id)

    if target == "all_users":
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == callback.from_user.id)
            )
            sender = result.scalar_one_or_none()
        if not sender or sender.role != UserRole.SUPER_ADMIN:
            await callback.answer(i18n_msg("only_sa_message_all", lang=lang), show_alert=True)
            return
    
    if target == "select":
        # Show list of subcontractors to select
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.role == UserRole.SUBCONTRACTOR)
            )
            subcontractors = list(result.scalars().all())
        
        if not subcontractors:
            await callback.message.edit_text(i18n_msg("no_subs_found", lang=lang))
            await state.clear()
            await callback.answer()
            return
        
        await state.update_data(target_type="select", selected_ids=[])
        await callback.message.edit_text(
            i18n_msg("select_subs_prompt", lang=lang),
            reply_markup=get_subcontractor_select_keyboard(subcontractors, [], lang=lang),
            parse_mode="Markdown"
        )
        await state.set_state(MessageStates.selecting_users)
    else:
        # Direct target (all_users, all_subs, northwest, southeast)
        await state.update_data(target_type=target)
        await callback.message.edit_text(
            i18n_msg("compose_message_prompt", lang=lang),
            parse_mode="Markdown"
        )
        await state.set_state(MessageStates.composing_message)
    await callback.answer()

@router.callback_query(F.data.startswith("msg_select:"), StateFilter(MessageStates.selecting_users))
async def toggle_user_selection(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected_ids = data.get('selected_ids', [])
    
    if user_id in selected_ids:
        selected_ids.remove(user_id)
    else:
        selected_ids.append(user_id)
    
    await state.update_data(selected_ids=selected_ids)
    
    # Refresh the keyboard
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.SUBCONTRACTOR)
        )
        subcontractors = list(result.scalars().all())
    
    await callback.message.edit_reply_markup(
        reply_markup=get_subcontractor_select_keyboard(subcontractors, selected_ids)
    )
    await callback.answer()

@router.callback_query(F.data == "msg_send", StateFilter(MessageStates.selecting_users))
async def proceed_to_compose(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_ids = data.get('selected_ids', [])
    
    if not selected_ids:
        await callback.answer("Please select at least one subcontractor", show_alert=True)
        return
    
    lang = await get_recipient_lang(callback.from_user.id)
    await callback.message.edit_text(
        i18n_msg("compose_message_selected", lang=lang, count=len(selected_ids)),
        parse_mode="Markdown"
    )
    await state.set_state(MessageStates.composing_message)
    await callback.answer()

@router.message(StateFilter(MessageStates.composing_message))
async def send_broadcast_message(message: Message, state: FSMContext):
    lang = await get_recipient_lang(message.from_user.id)
    if message.text.startswith("/"):
        await message.answer(i18n_msg("message_cancelled_msg", lang=lang))
        await state.clear()
        return
    
    data = await state.get_data()
    target_type = data.get('target_type')
    selected_ids = data.get('selected_ids', [])
    
    bot = message.bot
    sent_count = 0
    
    from src.bot.utils.keyboards import get_message_reaction_keyboard
    
    async with async_session() as session:
        # Get sender info
        sender_result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        sender = sender_result.scalar_one_or_none()
        sender_name = sender.first_name or sender.username or "Admin" if sender else "Admin"
        
        # Determine recipients
        if target_type == "select":
            result = await session.execute(
                select(User).where(User.id.in_(selected_ids))
            )
            recipients = list(result.scalars().all())
        elif target_type == "all_users":
            result = await session.execute(
                select(User).where(User.is_active == True)
            )
            recipients = [u for u in list(result.scalars().all()) if u.telegram_id != message.from_user.id]
        elif target_type == "all_subs":
            result = await session.execute(
                select(User).where(User.role == UserRole.SUBCONTRACTOR)
            )
            recipients = list(result.scalars().all())
        else:
            # Team-specific (northwest or southeast)
            team_result = await session.execute(
                select(Team).where(Team.team_type == TeamType(target_type))
            )
            team = team_result.scalar_one_or_none()
            if team:
                result = await session.execute(
                    select(User).where(
                        User.role == UserRole.SUBCONTRACTOR,
                        User.team_id == team.id
                    )
                )
                recipients = list(result.scalars().all())
            else:
                recipients = []
        
        # Determine team_id for storage
        team_id = None
        if target_type not in ["select", "all_subs", "all_users"]:
            try:
                team_id = team.id if team else None
            except:
                team_id = None
        
        # Save the broadcast message to database
        broadcast = BroadcastMessage(
            sender_id=sender.id if sender else None,
            message=message.text,
            target_role=("ALL_USERS" if target_type == "all_users" else "SUBCONTRACTOR"),
            target_team_id=team_id,
            recipient_ids=",".join(map(str, [r.id for r in recipients]))
        )
        session.add(broadcast)
        await session.flush()  # Get the broadcast ID
        
        from src.bot.utils.translate import translate_text
        _body_cache: dict[str, str] = {}
        for recipient in recipients:
            try:
                r_lang = await get_recipient_lang(recipient.telegram_id)
                if r_lang not in _body_cache:
                    _body_cache[r_lang] = await translate_text(message.text, target_lang=r_lang)
                header = i18n_msg("broadcast_header", lang=r_lang, sender=sender_name)
                body = _body_cache[r_lang]
                await bot.send_message(
                    recipient.telegram_id,
                    header + body,
                    reply_markup=get_message_reaction_keyboard(broadcast.id, lang=r_lang),
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to {recipient.telegram_id}: {e}")
        
        await session.commit()
    
    await message.answer(
        i18n_msg("message_sent_confirm", lang=lang, count=sent_count),
        parse_mode="Markdown"
    )
    await state.clear()


@router.message(F.text.in_(tv("Request Availability")))
async def btn_request_availability(message: Message, state: FSMContext):
    """Manager-only flow to request weekly availability from selected subcontractors."""
    if not async_session:
        lang = await get_recipient_lang(message.from_user.id)
        await message.answer(i18n_msg("db_unavailable", lang=lang))
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user or user.role != UserRole.ADMIN:
            lang = (getattr(user, "language", "en") or "en") if user else "en"
            await message.answer(i18n_msg("only_managers_request_avail", lang=lang))
            return

        subs_result = await session.execute(
            select(User).where(User.role == UserRole.SUBCONTRACTOR, User.is_active == True)
        )
        subcontractors = list(subs_result.scalars().all())

    lang = await get_recipient_lang(message.from_user.id)
    if not subcontractors:
        await message.answer(i18n_msg("no_subs_found", lang=lang))
        return

    await state.update_data(selected_ids=[])
    await message.answer(
        i18n_msg("request_avail_prompt", lang=lang),
        reply_markup=get_availability_request_select_keyboard(subcontractors, [], lang=lang),
        parse_mode="Markdown"
    )
    await state.set_state(AvailabilityRequestStates.selecting_users)


@router.callback_query(F.data.startswith("avail_req_select:"), StateFilter(AvailabilityRequestStates.selecting_users))
async def toggle_availability_request_selection(callback: CallbackQuery, state: FSMContext):
    if not async_session:
        lang = await get_recipient_lang(callback.from_user.id)
        await callback.answer(i18n_msg("db_unavailable", lang=lang), show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected_ids = data.get("selected_ids", [])

    if user_id in selected_ids:
        selected_ids.remove(user_id)
    else:
        selected_ids.append(user_id)

    await state.update_data(selected_ids=selected_ids)

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.SUBCONTRACTOR, User.is_active == True)
        )
        subcontractors = list(result.scalars().all())

    lang = await get_recipient_lang(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=get_availability_request_select_keyboard(subcontractors, selected_ids, lang=lang)
    )
    await callback.answer()


@router.callback_query(F.data == "avail_req_cancel", StateFilter(AvailabilityRequestStates.selecting_users))
async def cancel_availability_request(callback: CallbackQuery, state: FSMContext):
    lang = await get_recipient_lang(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(i18n_msg("avail_req_cancelled", lang=lang))
    await callback.answer()


@router.callback_query(F.data == "avail_req_send", StateFilter(AvailabilityRequestStates.selecting_users))
async def send_availability_request(callback: CallbackQuery, state: FSMContext):
    if not async_session:
        lang = await get_recipient_lang(callback.from_user.id)
        await callback.answer(i18n_msg("db_unavailable", lang=lang), show_alert=True)
        return

    data = await state.get_data()
    selected_ids = data.get("selected_ids", [])
    if not selected_ids:
        lang = await get_recipient_lang(callback.from_user.id)
        await callback.answer(i18n_msg("select_at_least_one", lang=lang), show_alert=True)
        return

    from datetime import datetime, timedelta

    bot = callback.bot
    sent_count = 0
    failed_count = 0

    today = datetime.utcnow().date()
    days_since_monday = today.weekday()
    current_monday = datetime.combine(today - timedelta(days=days_since_monday), datetime.min.time())

    async with async_session() as session:
        requester_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        requester = requester_result.scalar_one_or_none()
        if not requester or requester.role != UserRole.ADMIN:
            lang = await get_recipient_lang(callback.from_user.id)
            await callback.answer(i18n_msg("only_managers_request_avail", lang=lang), show_alert=True)
            return

        result = await session.execute(
            select(User).where(
                User.id.in_(selected_ids),
                User.role == UserRole.SUBCONTRACTOR,
                User.is_active == True,
            )
        )
        recipients = list(result.scalars().all())

        for sub in recipients:
            avail_result = await session.execute(
                select(WeeklyAvailability).where(
                    WeeklyAvailability.subcontractor_id == sub.id,
                    WeeklyAvailability.week_start == current_monday,
                )
            )
            availability = avail_result.scalar_one_or_none()
            if not availability:
                availability = WeeklyAvailability(
                    subcontractor_id=sub.id,
                    week_start=current_monday,
                )
                session.add(availability)
                await session.flush()

            selected_days = []
            if availability.monday_available:
                selected_days.append("mon")
            if availability.tuesday_available:
                selected_days.append("tue")
            if availability.wednesday_available:
                selected_days.append("wed")
            if availability.thursday_available:
                selected_days.append("thu")
            if availability.friday_available:
                selected_days.append("fri")

            mon_date = current_monday.strftime("%d/%m")
            tue_date = (current_monday + timedelta(days=1)).strftime("%d/%m")
            wed_date = (current_monday + timedelta(days=2)).strftime("%d/%m")
            thu_date = (current_monday + timedelta(days=3)).strftime("%d/%m")
            fri_date = (current_monday + timedelta(days=4)).strftime("%d/%m")

            try:
                sub_lang = await get_recipient_lang(sub.telegram_id)
                avail_text = i18n_msg(
                    "availability_request", lang=sub_lang,
                    mon=mon_date, tue=tue_date, wed=wed_date,
                    thu=thu_date, fri=fri_date
                )
                await bot.send_message(
                    sub.telegram_id,
                    avail_text,
                    reply_markup=get_weekly_availability_keyboard(availability.id, selected_days),
                    parse_mode="Markdown",
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send availability request to {sub.telegram_id}: {e}")
                failed_count += 1

        await session.commit()

    lang = await get_recipient_lang(callback.from_user.id)
    await callback.message.edit_text(
        i18n_msg("avail_requests_sent", lang=lang, requested=len(selected_ids), sent=sent_count, failed=failed_count),
        parse_mode="Markdown",
    )
    await state.clear()
    await callback.answer()

# ============= WEEKLY AVAILABILITY VIEW =============

@router.message(F.text.in_(tv("Weekly Availability")))
async def btn_weekly_availability(message: Message):
    """View weekly availability responses for all subcontractors"""
    if not async_session:
        lang = await get_recipient_lang(message.from_user.id)
        await message.answer(i18n_msg("db_unavailable", lang=lang))
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    lang = await get_recipient_lang(message.from_user.id)
    if not user or user.role != UserRole.ADMIN:
        await message.answer(i18n_msg("only_managers_view_avail", lang=lang))
        return
    
    from datetime import datetime, timedelta
    
    # Get current week's Monday
    today = datetime.utcnow().date()
    days_since_monday = today.weekday()
    current_monday = datetime.combine(today - timedelta(days=days_since_monday), datetime.min.time())
    
    async with async_session() as session:
        # Get all availability records for this week
        result = await session.execute(
            select(WeeklyAvailability, User).join(
                User, WeeklyAvailability.subcontractor_id == User.id
            ).where(WeeklyAvailability.week_start == current_monday)
        )
        responses = list(result.all())
        
        if not responses:
            await message.answer(i18n_msg("weekly_avail_empty", lang=lang), parse_mode="Markdown")
            return
        
        text = i18n_msg("weekly_avail_view_title", lang=lang, week=current_monday.strftime('%d/%m/%Y'))
        
        responded = []
        pending = []
        
        for avail, user in responses:
            name = user.first_name or user.username or f"User {user.telegram_id}"
            
            if avail.responded_at is None:
                pending.append(name)
            else:
                days_available = []
                if avail.monday_available:
                    days_available.append("Mon")
                if avail.tuesday_available:
                    days_available.append("Tue")
                if avail.wednesday_available:
                    days_available.append("Wed")
                if avail.thursday_available:
                    days_available.append("Thu")
                if avail.friday_available:
                    days_available.append("Fri")
                
                if days_available:
                    responded.append(f"*{name}:*  {', '.join(days_available)}")
                else:
                    responded.append(f"*{name}:*  Not available")
                
                if avail.notes:
                    responded[-1] += f"\n   _Notes: {avail.notes}_"
        
        if responded:
            text += "\n".join(responded) + "\n\n"
        
        if pending:
            text += i18n_msg("avail_pending_label", lang=lang, names=', '.join(pending))
        
        await message.answer(text, parse_mode="Markdown")

# ============= CUSTOM ROLES MANAGEMENT =============

class CreateRoleStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_base_role = State()
    selecting_permissions = State()

class CreateRegionStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()

class CreateTeamStates(StatesGroup):
    waiting_for_name = State()

from src.bot.database.models import Region, CustomRole, RolePermission, AVAILABLE_PERMISSIONS

@router.message(F.text.in_(tv("Manage Roles")))
@require_role(UserRole.SUPER_ADMIN)
async def show_manage_roles(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(CustomRole).where(CustomRole.is_active == True).order_by(CustomRole.name)
        )
        roles = list(result.scalars().all())
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=" Create New Role", callback_data="create_role"))
    
    for role in roles:
        keyboard.row(InlineKeyboardButton(
            text=f" {role.name}", 
            callback_data=f"view_role:{role.id}"
        ))
    
    await message.answer(
        "* Manage Custom Roles*\n\n"
        f"You have {len(roles)} custom role(s).\n\n"
        "Custom roles let you define specific permissions for users.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "create_role")
async def start_create_role(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "*Create Custom Role*\n\n"
        "Enter the name for this new role:",
        parse_mode="Markdown"
    )
    await state.set_state(CreateRoleStates.waiting_for_name)
    await callback.answer()

@router.message(StateFilter(CreateRoleStates.waiting_for_name))
async def process_role_name(message: Message, state: FSMContext):
    await state.update_data(role_name=message.text.strip())
    await message.answer(
        "Enter a description for this role (or send /skip):",
        parse_mode="Markdown"
    )
    await state.set_state(CreateRoleStates.waiting_for_description)

@router.message(StateFilter(CreateRoleStates.waiting_for_description))
async def process_role_description(message: Message, state: FSMContext):
    description = None if message.text == "/skip" else message.text.strip()
    await state.update_data(role_description=description)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Supervisor-based", callback_data="base_role:supervisor")],
        [InlineKeyboardButton(text=" Subcontractor-based", callback_data="base_role:subcontractor")],
        [InlineKeyboardButton(text=" Cancel", callback_data="cancel_role_create")]
    ])
    
    await message.answer(
        "*Select Base Role*\n\n"
        "Choose which role type this custom role is based on:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(CreateRoleStates.waiting_for_base_role)

@router.callback_query(F.data.startswith("base_role:"))
async def process_base_role(callback: CallbackQuery, state: FSMContext):
    base = callback.data.split(":")[1]
    base_role = UserRole.SUPERVISOR if base == "supervisor" else UserRole.SUBCONTRACTOR
    await state.update_data(base_role=base_role.value, selected_permissions=[])
    
    keyboard = await build_permission_keyboard([])
    
    await callback.message.answer(
        "*Select Permissions*\n\n"
        "Tap permissions to toggle them on/off.\n"
        " = Enabled,  = Disabled\n\n"
        "When done, tap *Save Role*.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(CreateRoleStates.selecting_permissions)
    await callback.answer()

async def build_permission_keyboard(selected: list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    for key, label in AVAILABLE_PERMISSIONS:
        status = "" if key in selected else ""
        keyboard.row(InlineKeyboardButton(
            text=f"{status} {label}",
            callback_data=f"toggle_perm:{key}"
        ))
    
    keyboard.row(
        InlineKeyboardButton(text=" Save Role", callback_data="save_custom_role"),
        InlineKeyboardButton(text=" Cancel", callback_data="cancel_role_create")
    )
    
    return keyboard.as_markup()

@router.callback_query(F.data.startswith("toggle_perm:"))
async def toggle_permission(callback: CallbackQuery, state: FSMContext):
    perm_key = callback.data.split(":")[1]
    data = await state.get_data()
    selected = data.get("selected_permissions", [])
    
    if perm_key in selected:
        selected.remove(perm_key)
    else:
        selected.append(perm_key)
    
    await state.update_data(selected_permissions=selected)
    keyboard = await build_permission_keyboard(selected)
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"Toggled {perm_key}")

@router.callback_query(F.data == "save_custom_role")
async def save_custom_role(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    role_name = data.get("role_name")
    role_description = data.get("role_description")
    base_role = UserRole(data.get("base_role"))
    selected_permissions = data.get("selected_permissions", [])
    
    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        custom_role = CustomRole(
            name=role_name,
            description=role_description,
            base_role=base_role,
            created_by_id=user.id if user else None
        )
        session.add(custom_role)
        await session.flush()
        
        for perm_key in selected_permissions:
            permission = RolePermission(
                custom_role_id=custom_role.id,
                permission_key=perm_key,
                enabled=True
            )
            session.add(permission)
        
        await session.commit()
    
    await callback.message.answer(
        f"* Role Created!*\n\n"
        f"*Name:* {role_name}\n"
        f"*Base:* {base_role.value.title()}\n"
        f"*Permissions:* {len(selected_permissions)} enabled\n\n"
        "You can now create access codes with this custom role.",
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("view_role:"))
async def view_custom_role(callback: CallbackQuery):
    role_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(CustomRole).where(CustomRole.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            await callback.answer("Role not found.")
            return
        
        perm_result = await session.execute(
            select(RolePermission).where(
                RolePermission.custom_role_id == role_id,
                RolePermission.enabled == True
            )
        )
        permissions = list(perm_result.scalars().all())
    
    perm_names = []
    perm_dict = {k: v for k, v in AVAILABLE_PERMISSIONS}
    for p in permissions:
        if p.permission_key in perm_dict:
            perm_names.append(perm_dict[p.permission_key])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Delete Role", callback_data=f"delete_role:{role_id}")],
        [InlineKeyboardButton(text=" Back", callback_data="back_to_roles")]
    ])
    
    await callback.message.answer(
        f"* {role.name}*\n\n"
        f"*Base Role:* {role.base_role.value.title()}\n"
        f"*Description:* {role.description or 'None'}\n\n"
        f"*Enabled Permissions:*\n" + 
        ("\n".join([f" {p}" for p in perm_names]) if perm_names else "None"),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_role:"))
async def delete_custom_role(callback: CallbackQuery):
    role_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(CustomRole).where(CustomRole.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if role:
            role.is_active = False
            await session.commit()
    
    await callback.message.answer(" Role deleted.")
    await callback.answer()

@router.callback_query(F.data == "cancel_role_create")
async def cancel_role_create(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Role creation cancelled.")
    await callback.answer()

# ============= REGIONS MANAGEMENT =============

@router.message(F.text.in_(tv("Manage Regions")))
@require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN)
async def show_manage_regions(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Region).where(Region.is_active == True).order_by(Region.name)
        )
        regions = list(result.scalars().all())
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=" Create New Region", callback_data="create_region"))
    
    for region in regions:
        keyboard.row(InlineKeyboardButton(
            text=f" {region.name}", 
            callback_data=f"view_region:{region.id}"
        ))
    
    await message.answer(
        "* Manage Regions*\n\n"
        f"You have {len(regions)} region(s).\n\n"
        "Regions let you organize users and jobs by geographic area.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

@router.message(F.text.in_(tv("View Regions")))
@require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN)
async def view_regions_list(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Region).where(Region.is_active == True).order_by(Region.name)
        )
        regions = list(result.scalars().all())
        
        if not regions:
            await message.answer(
                "* Regions*\n\n"
                "No regions created yet.\n"
                "Use *Manage Regions* to create regions.",
                parse_mode="Markdown"
            )
            return
        
        text = "* All Regions*\n\n"
        for region in regions:
            user_count = await session.execute(
                select(User).where(User.region_id == region.id, User.is_active == True)
            )
            count = len(list(user_count.scalars().all()))
            text += f" *{region.name}* - {count} user(s)\n"
            if region.description:
                text += f"  _{region.description}_\n"
        
        await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "create_region")
async def start_create_region(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "*Create Region*\n\n"
        "Enter the name for this region (e.g., London, Manchester):",
        parse_mode="Markdown"
    )
    await state.set_state(CreateRegionStates.waiting_for_name)
    await callback.answer()

@router.message(StateFilter(CreateRegionStates.waiting_for_name))
async def process_region_name(message: Message, state: FSMContext):
    await state.update_data(region_name=message.text.strip())
    await message.answer(
        "Enter a description for this region (or send /skip):",
        parse_mode="Markdown"
    )
    await state.set_state(CreateRegionStates.waiting_for_description)

@router.message(StateFilter(CreateRegionStates.waiting_for_description))
async def process_region_description(message: Message, state: FSMContext):
    data = await state.get_data()
    region_name = data.get("region_name")
    description = None if message.text == "/skip" else message.text.strip()
    
    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        region = Region(
            name=region_name,
            description=description,
            created_by_id=user.id if user else None
        )
        session.add(region)
        await session.commit()
    
    await message.answer(
        f"* Region Created!*\n\n"
        f"*Name:* {region_name}\n"
        f"*Description:* {description or 'None'}\n\n"
        "You can now assign users to this region when creating access codes.",
        parse_mode="Markdown"
    )
    await state.clear()

@router.callback_query(F.data.startswith("view_region:"))
async def view_region(callback: CallbackQuery):
    region_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(Region).where(Region.id == region_id)
        )
        region = result.scalar_one_or_none()
        
        if not region:
            await callback.answer("Region not found.")
            return
        
        user_result = await session.execute(
            select(User).where(User.region_id == region_id, User.is_active == True)
        )
        users = list(user_result.scalars().all())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Delete Region", callback_data=f"delete_region:{region_id}")],
        [InlineKeyboardButton(text=" Back", callback_data="back_to_regions")]
    ])
    
    user_list = "\n".join([
        f" {u.first_name or u.username or 'Unknown'} ({role_display_name(u.role)})"
        for u in users[:10]
    ])
    if len(users) > 10:
        user_list += f"\n... and {len(users) - 10} more"
    
    await callback.message.answer(
        f"* {region.name}*\n\n"
        f"*Description:* {region.description or 'None'}\n"
        f"*Users:* {len(users)}\n\n"
        f"*Users in this region:*\n{user_list or 'None'}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_region:"))
async def delete_region(callback: CallbackQuery):
    region_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(Region).where(Region.id == region_id)
        )
        region = result.scalar_one_or_none()
        
        if region:
            region.is_active = False
            await session.commit()
    
    await callback.message.answer(" Region deleted.")
    await callback.answer()

# ============= TEAMS MANAGEMENT =============

@router.message(F.text.in_(tv("Manage Teams")))
@require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN)
async def show_manage_teams(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Team).order_by(Team.name)
        )
        teams = list(result.scalars().all())
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=" Create New Team", callback_data="create_team"))
    
    for team in teams:
        keyboard.row(InlineKeyboardButton(
            text=f" {team.name}", 
            callback_data=f"view_team:{team.id}"
        ))
    
    await message.answer(
        "* Manage Teams*\n\n"
        f"You have {len(teams)} team(s).\n\n"
        "Teams help organize subcontractors into groups.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "create_team")
async def start_create_team(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "*Create Team*\n\n"
        "Enter the name for this team:",
        parse_mode="Markdown"
    )
    await state.set_state(CreateTeamStates.waiting_for_name)
    await callback.answer()

@router.message(StateFilter(CreateTeamStates.waiting_for_name))
async def process_team_name(message: Message, state: FSMContext):
    team_name = message.text.strip()
    
    async with async_session() as session:
        existing = await session.execute(
            select(Team).where(Team.name == team_name)
        )
        if existing.scalar_one_or_none():
            await message.answer("A team with this name already exists. Please choose a different name.")
            return
        
        team = Team(name=team_name)
        session.add(team)
        await session.commit()
    
    await message.answer(
        f"* Team Created!*\n\n"
        f"*Name:* {team_name}\n\n"
        "You can now assign users to this team when creating access codes.",
        parse_mode="Markdown"
    )
    await state.clear()

@router.callback_query(F.data.startswith("view_team:"))
async def view_team_details(callback: CallbackQuery):
    team_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(Team).where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            await callback.answer("Team not found.")
            return
        
        user_result = await session.execute(
            select(User).where(User.team_id == team_id, User.is_active == True)
        )
        users = list(user_result.scalars().all())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Delete Team", callback_data=f"delete_team:{team_id}")],
        [InlineKeyboardButton(text=" Back", callback_data="back_to_teams")]
    ])
    
    user_list = "\n".join([
        f" {u.first_name or u.username or 'Unknown'} ({role_display_name(u.role)})"
        for u in users[:10]
    ])
    if len(users) > 10:
        user_list += f"\n... and {len(users) - 10} more"
    
    await callback.message.answer(
        f"* {team.name}*\n\n"
        f"*Users:* {len(users)}\n\n"
        f"*Members:*\n{user_list or 'None'}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_team:"))
async def delete_team(callback: CallbackQuery):
    team_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(Team).where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if team:
            await session.delete(team)
            await session.commit()
    
    await callback.message.answer(" Team deleted.")
    await callback.answer()



