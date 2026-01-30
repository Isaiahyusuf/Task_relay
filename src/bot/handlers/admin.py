from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from src.bot.database import async_session, User, Job
from src.bot.database.models import UserRole, JobStatus, JobType
from src.bot.services.jobs import JobService
from src.bot.services.archive import ArchiveService
from src.bot.services.access_codes import AccessCodeService
from src.bot.utils.permissions import require_role
from src.bot.utils.keyboards import (
    get_role_selection_keyboard, get_job_list_keyboard, get_back_keyboard,
    get_user_list_keyboard, get_user_actions_keyboard, get_switch_role_keyboard,
    get_confirm_delete_keyboard, get_main_menu_keyboard, get_supervisor_job_actions_keyboard,
    get_confirm_job_delete_keyboard
)
import logging
import sqlalchemy

logger = logging.getLogger(__name__)
router = Router()

class CreateCodeStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_role = State()
    waiting_for_team = State()
    confirming = State()

@router.message(Command("history"))
@require_role(UserRole.ADMIN)
async def cmd_history(message: Message):
    await show_history(message)

@router.message(F.text == "📊 Job History")
async def btn_history(message: Message):
    if not await check_admin(message):
        return
    await show_history(message)

async def check_admin(message: Message) -> bool:
    if not async_session:
        await message.answer("Database not available.")
        return False
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            await message.answer("You don't have admin permissions.")
            return False
    return True

async def check_super_admin(message: Message) -> bool:
    if not async_session:
        await message.answer("Database not available.")
        return False
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != UserRole.SUPER_ADMIN:
            await message.answer("You don't have super admin permissions.")
            return False
    return True

async def show_history(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    jobs = await JobService.get_job_history(team_id=user.team_id if user else None, limit=50)
    
    if not jobs:
        await message.answer(
            "*Job History*\n\n"
            "No job records found.",
            parse_mode="Markdown"
        )
        return
    
    status_counts = {}
    for job in jobs:
        status = job.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    summary = "\n".join([f"  {status.replace('_', ' ').title()}: {count}" for status, count in status_counts.items()])
    
    await message.answer(
        f"*Job History*\n\n"
        f"*Summary ({len(jobs)} jobs):*\n{summary}\n\n"
        "Select a job to view details:",
        reply_markup=get_job_list_keyboard(jobs, context="history"),
        parse_mode="Markdown"
    )

@router.message(Command("archive"))
@require_role(UserRole.ADMIN)
async def cmd_archive(message: Message):
    await archive_jobs(message)

@router.message(F.text == "📦 Archive Jobs")
async def btn_archive(message: Message):
    if not await check_admin(message):
        return
    await archive_jobs(message)

async def archive_jobs(message: Message):
    count = await ArchiveService.archive_old_jobs()
    
    if count > 0:
        await message.answer(
            f"*Archive Complete*\n\n"
            f"Archived *{count}* old jobs.\n\n"
            "Archived jobs can be viewed in 'View Archived'.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "*Archive Jobs*\n\n"
            "No jobs eligible for archiving at this time.\n\n"
            "Jobs are automatically archived after 90 days.",
            parse_mode="Markdown"
        )

@router.message(Command("archived"))
@require_role(UserRole.ADMIN)
async def cmd_archived(message: Message):
    await show_archived(message)

@router.message(F.text == "📋 View Archived")
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
    
    jobs = await ArchiveService.get_archived_jobs(team_id=user.team_id if user else None)
    
    if not jobs:
        await message.answer(
            "*Archived Jobs*\n\n"
            "No archived jobs found.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        f"*Archived Jobs* ({len(jobs)} total)\n\n"
        "Select a job to view details:",
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
        
        if role_str not in role_map:
            await message.answer(
                "Invalid role. Use: admin, supervisor, or subcontractor"
            )
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
            await message.answer(
                f"*Access Code Created*\n\n"
                f"Code: `{code}`\n"
                f"Role: {role_str.title()}\n\n"
                "Share this code privately with the intended user.",
                parse_mode="Markdown"
            )
        else:
            await message.answer("Failed to create code. It may already exist.")
        return
    
    await start_code_creation(message, state)

@router.message(F.text == "🔑 Create Access Code")
async def btn_create_code(message: Message, state: FSMContext):
    if not await check_admin(message):
        return
    await start_code_creation(message, state)

async def start_code_creation(message: Message, state: FSMContext):
    await message.answer(
        "*Create Access Code*\n\n"
        "Step 1/2: Enter the access code\n"
        "(letters and numbers only):",
        parse_mode="Markdown"
    )
    await state.set_state(CreateCodeStates.waiting_for_code)

MENU_BUTTON_TEXTS = {
    "👔 View Supervisors", "🔧 View Subcontractors", "👑 View Admins",
    "👥 All Users", "🔑 All Access Codes", "🔑 Create Access Code",
    "📋 View Jobs", "➕ Create Job", "📜 Job History", "🏠 Main Menu",
    "⬅️ Back", "❌ Cancel"
}

@router.message(StateFilter(CreateCodeStates.waiting_for_code), ~F.text.in_(MENU_BUTTON_TEXTS))
async def process_code_input(message: Message, state: FSMContext):
    code = message.text.strip()
    
    if not code.isalnum():
        await message.answer("Code must contain only letters and numbers. Try again:")
        return
    
    if len(code) < 4:
        await message.answer("Code must be at least 4 characters. Try again:")
        return
    
    data = await state.get_data()
    forced_role = data.get("forced_role")
    
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
            team_id=user.team_id if user else None
        )
        
        if success:
            await message.answer(
                f"*Access Code Created!*\n\n"
                f"Code: `{code}`\n"
                f"Role: {forced_role.value.title()}\n\n"
                "Share this code privately with the intended subcontractor.",
                parse_mode="Markdown"
            )
        else:
            await message.answer("Failed to create code. It may already exist.")
        
        await state.clear()
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
        "*Create Access Code*\n\n"
        f"Code: `{code}`\n\n"
        "Step 2/2: Select the role for this code:",
        reply_markup=get_role_selection_keyboard(creator_role=creator_role),
        parse_mode="Markdown"
    )
    await state.set_state(CreateCodeStates.waiting_for_role)

@router.callback_query(F.data.startswith("role:"), StateFilter(CreateCodeStates.waiting_for_role))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    role_str = callback.data.split(":")[1]
    
    role_map = {
        "super_admin": UserRole.SUPER_ADMIN,
        "admin": UserRole.ADMIN,
        "supervisor": UserRole.SUPERVISOR,
        "subcontractor": UserRole.SUBCONTRACTOR
    }
    
    await state.update_data(role=role_map[role_str], role_str=role_str)
    
    # Ask for team assignment for admin, supervisor, and subcontractor
    if role_str in ["admin", "supervisor", "subcontractor"]:
        from src.bot.utils.keyboards import get_team_selection_keyboard
        role_label = role_str.title()
        await callback.message.edit_text(
            f"*Select Team*\n\n"
            f"Which team should this {role_label} be assigned to?",
            reply_markup=get_team_selection_keyboard(for_code=True),
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
    from src.bot.database.models import TeamType, Team
    
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
    
    success = await AccessCodeService.create_access_code(
        code=code,
        role=role,
        team_id=team_id
    )
    
    if success:
        team_info = f"Team: {team_name}\n" if team_name else ""
        await callback.message.edit_text(
            f"*Access Code Created!*\n\n"
            f"Code: `{code}`\n"
            f"Role: {role_str.title()}\n"
            f"{team_info}\n"
            "Share this code privately with the intended user.\n"
            "They can use it with /start to register.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            f"Failed to create code.\n\n"
            "The code may already exist."
        )
    
    await state.clear()

@router.callback_query(F.data == "cancel_code")
async def cancel_code_from_team(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Access code creation cancelled.")
    await callback.answer()

@router.callback_query(F.data == "code_cancel")
async def cancel_code_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Access code creation cancelled.")
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
    
    if not await check_admin(callback.message):
        await callback.answer("Not authorized", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ *Delete Job #{job_id}*\n\n"
        "Are you sure you want to delete this job record completely?\n"
        "*This action cannot be undone.*",
        reply_markup=get_confirm_job_delete_keyboard(job_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_job_delete:"))
async def handle_confirm_job_delete(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        # Check admin again
        admin_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        admin = admin_result.scalar_one_or_none()
        if not admin or admin.role != UserRole.ADMIN:
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

    await callback.message.edit_text(
        f"✅ Job #{job_id} and all associated quotes have been deleted.",
        reply_markup=get_back_keyboard("back:history")
    )
    await callback.answer()

@router.callback_query(F.data == "back:history")
async def back_to_history(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    jobs = await JobService.get_job_history(team_id=user.team_id if user else None, limit=50)
    
    status_counts = {}
    for job in jobs:
        status = job.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    summary = "\n".join([f"  {status.replace('_', ' ').title()}: {count}" for status, count in status_counts.items()])
    
    await callback.message.edit_text(
        f"*Job History*\n\n"
        f"*Summary ({len(jobs)} jobs):*\n{summary}\n\n"
        "Select a job to view details:",
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
    
    jobs = await ArchiveService.get_archived_jobs(team_id=user.team_id if user else None)
    
    await callback.message.edit_text(
        f"*Archived Jobs* ({len(jobs)} total)\n\n"
        "Select a job to view details:",
        reply_markup=get_job_list_keyboard(jobs, context="archived"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(F.text == "👥 Manage Users")
async def btn_manage_users(message: Message):
    if not await check_admin(message):
        return
    await show_user_list(message)

async def show_all_access_codes(message: Message):
    from src.bot.database import AccessCode
    
    async with async_session() as session:
        result = await session.execute(
            select(AccessCode).where(
                AccessCode.is_active == True,
                AccessCode.current_uses < AccessCode.max_uses
            ).order_by(AccessCode.role, AccessCode.code)
        )
        codes = list(result.scalars().all())
    
    if not codes:
        await message.answer(
            "*All Access Codes*\n\n"
            "No available access codes found.\n\n"
            "Use 'Create Access Code' to create new codes.",
            parse_mode="Markdown"
        )
        return
    
    code_text = ""
    for code in codes:
        role_emoji = {"admin": "👑", "supervisor": "👔", "subcontractor": "🔧", "super_admin": "🦸"}.get(code.role.value, "👤")
        code_text += f"{role_emoji} `{code.code}` - {code.role.value.replace('_', ' ').title()}\n"
    
    await message.answer(
        f"*All Access Codes* ({len(codes)} available)\n\n"
        f"{code_text}\n"
        "Share these codes privately with intended users.",
        parse_mode="Markdown"
    )

@router.message(F.text == "👑 View Admins")
async def btn_view_admins(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_users_by_role(message, UserRole.ADMIN, "Admins")

@router.message(F.text == "👔 View Supervisors")
async def btn_view_supervisors(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_users_by_role(message, UserRole.SUPERVISOR, "Supervisors")

@router.message(F.text == "🔧 View Subcontractors")
async def btn_view_subcontractors(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_users_by_role(message, UserRole.SUBCONTRACTOR, "Subcontractors")

@router.message(F.text == "🔑 All Access Codes")
async def btn_all_access_codes_v2(message: Message, state: FSMContext):
    await state.clear()
    if not await check_super_admin(message):
        return
    await show_all_access_codes(message)

@router.message(F.text == "👥 All Users")
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
    
    if not users:
        await message.answer(
            f"*{role_name}*\n\n"
            f"No {role_name.lower()} found.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        f"*{role_name}* ({len(users)} total)\n\n"
        "Select a user to manage:",
        reply_markup=get_user_list_keyboard(users, is_super_admin=True),
        parse_mode="Markdown"
    )

@router.message(F.text == "🔄 Switch Role")
async def btn_switch_role_super_admin(message: Message, state: FSMContext):
    await state.clear()
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    if not user:
        await message.answer("User not found.")
        return
    
    # Check if super admin or has super admin code
    if user.role == UserRole.SUPER_ADMIN:
        from src.bot.utils.keyboards import get_super_admin_switch_role_keyboard
        await message.answer(
            "*Switch Role*\n\n"
            "As Super Admin, you can temporarily switch to any role.\n"
            "You can always switch back using the super admin code.\n\n"
            "Select a role:",
            reply_markup=get_super_admin_switch_role_keyboard(),
            parse_mode="Markdown"
        )
    elif user.super_admin_code:
        # User was a super admin, show return option
        await message.answer(
            "*Switch Role*\n\n"
            "You can return to Super Admin using the button below.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🦸 Return to Super Admin", callback_data="sa_switch:super_admin")],
                [InlineKeyboardButton(text="❌ Cancel", callback_data="back:main")]
            ]),
            parse_mode="Markdown"
        )
    elif user.role == UserRole.ADMIN:
        await message.answer(
            "*Switch Role*\n\n"
            "Select a role to switch to:",
            reply_markup=get_switch_role_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer("You don't have permission to switch roles.")

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
        
        if role_str == "super_admin":
            # Return to super admin
            if user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE:
                user.role = UserRole.SUPER_ADMIN
                await session.commit()
                
                await callback.message.edit_text(
                    "✅ *Welcome back, Super Admin!*\n\n"
                    "You have returned to Super Admin role.",
                    parse_mode="Markdown"
                )
                keyboard = get_main_menu_keyboard(UserRole.SUPER_ADMIN)
                await callback.message.answer(
                    "Use the menu below:",
                    reply_markup=keyboard
                )
            else:
                await callback.answer("Cannot return to Super Admin - code has changed", show_alert=True)
        else:
            # Switch to another role
            if user.role != UserRole.SUPER_ADMIN and not user.super_admin_code:
                await callback.answer("Not authorized", show_alert=True)
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
            
            user.role = new_role
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ *Role Changed*\n\n"
                f"You are now a *{role_str.title()}*.\n\n"
                f"You can return to Super Admin anytime by using 'Switch Role' or entering the super admin code.",
                parse_mode="Markdown"
            )
            keyboard = get_main_menu_keyboard(new_role)
            await callback.message.answer(
                "Use the menu below:",
                reply_markup=keyboard
            )
    
    await callback.answer()

@router.callback_query(F.data == "back:sa_menu")
async def back_to_super_admin_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.message(F.text == "🦸 Return to Super Admin")
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
        
        if user.super_admin_code and user.super_admin_code == config.SUPER_ADMIN_CODE:
            user.role = UserRole.SUPER_ADMIN
            await session.commit()
            
            keyboard = get_main_menu_keyboard(UserRole.SUPER_ADMIN)
            await message.answer(
                "✅ *Welcome back, Super Admin!*\n\n"
                "You have returned to Super Admin role.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await message.answer("Cannot return to Super Admin - code has changed or you were never a super admin.")

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
    
    if not users:
        await message.answer("No users found.")
        return
    
    title = "Manage All Users (Super Admin)" if is_super_admin else "Manage Users"
    await message.answer(
        f"*{title}* ({len(users)} total)\n\n"
        "Select a user to manage:",
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
        role_text = user.role.value.title()
        name = user.first_name or user.username or f"User {user.telegram_id}"
        username = user.username or 'N/A'
        is_active = user.is_active
        created_date = user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'
    
    await callback.message.edit_text(
        f"*User Details*\n\n"
        f"*Name:* {name}\n"
        f"*Username:* @{username}\n"
        f"*Role:* {role_text}\n"
        f"*Status:* {'Active' if is_active else 'Inactive'}\n"
        f"*Joined:* {created_date}\n\n"
        f"{'⚠️ This is your own account.' if is_self else ''}",
        reply_markup=get_user_actions_keyboard(user_id, is_self),
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
    
    if delete_type == "self":
        warning = (
            f"⚠️ *Delete Your Account*\n\n"
            f"Are you sure you want to delete your own admin account?\n\n"
            f"*This action cannot be undone.*\n"
            f"You will be logged out and need a new access code to return."
        )
    else:
        warning = (
            f"⚠️ *Delete User*\n\n"
            f"Are you sure you want to delete *{name}*?\n\n"
            f"*This action cannot be undone.*"
        )
    
    await callback.message.edit_text(
        warning,
        reply_markup=get_confirm_delete_keyboard(user_id, delete_type),
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
    
    if is_self:
        await callback.message.edit_text(
            "Your account has been deleted.\n\n"
            "Use /start with a new access code to register again."
        )
    else:
        await callback.message.edit_text(
            f"*User Deleted*\n\n"
            f"{name} has been removed from the system.",
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
    
    await callback.message.edit_text(
        f"*Manage Users* ({len(users)} total)\n\n"
        "Select a user to manage:",
        reply_markup=get_user_list_keyboard(users),
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

@router.message(F.text == "🔄 Switch Role")
async def btn_switch_role(message: Message):
    if not await check_admin(message):
        return
    
    await message.answer(
        "*Switch Your Role*\n\n"
        "You are currently an Admin.\n\n"
        "⚠️ *Warning:* Switching roles will change your access level.\n"
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
