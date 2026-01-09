from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
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
    get_confirm_delete_keyboard, get_main_menu_keyboard
)
import logging

logger = logging.getLogger(__name__)
router = Router()

class CreateCodeStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_role = State()
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
        if not user or user.role != UserRole.ADMIN:
            await message.answer("You don't have admin permissions.")
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

@router.message(StateFilter(CreateCodeStates.waiting_for_code))
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

    await state.update_data(code=code)
    await message.answer(
        "*Create Access Code*\n\n"
        f"Code: `{code}`\n\n"
        "Step 2/2: Select the role for this code:",
        reply_markup=get_role_selection_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateCodeStates.waiting_for_role)

@router.callback_query(F.data.startswith("role:"), StateFilter(CreateCodeStates.waiting_for_role))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    role_str = callback.data.split(":")[1]
    data = await state.get_data()
    code = data.get('code')
    
    role_map = {
        "admin": UserRole.ADMIN,
        "supervisor": UserRole.SUPERVISOR,
        "subcontractor": UserRole.SUBCONTRACTOR
    }
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    success = await AccessCodeService.create_access_code(
        code=code,
        role=role_map[role_str],
        team_id=user.team_id if user else None
    )
    
    if success:
        await callback.message.edit_text(
            f"*Access Code Created!*\n\n"
            f"Code: `{code}`\n"
            f"Role: {role_str.title()}\n\n"
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
        reply_markup=get_back_keyboard(f"back:{context}"),
        parse_mode="Markdown"
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

async def show_user_list(message: Message):
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
    
    await message.answer(
        f"*Manage Users* ({len(users)} total)\n\n"
        "Select a user to manage:",
        reply_markup=get_user_list_keyboard(users),
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
        
        if not admin or admin.role != UserRole.ADMIN:
            await callback.answer("Not authorized", show_alert=True)
            return
        
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    
    if not user:
        await callback.answer("User not found", show_alert=True)
        return
    
    is_self = user.telegram_id == callback.from_user.id
    role_text = user.role.value.title()
    name = user.first_name or user.username or f"User {user.telegram_id}"
    
    await callback.message.edit_text(
        f"*User Details*\n\n"
        f"*Name:* {name}\n"
        f"*Username:* @{user.username or 'N/A'}\n"
        f"*Role:* {role_text}\n"
        f"*Status:* {'Active' if user.is_active else 'Inactive'}\n"
        f"*Joined:* {user.created_at.strftime('%Y-%m-%d')}\n\n"
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
        
        if not admin or admin.role != UserRole.ADMIN:
            await callback.answer("Not authorized", show_alert=True)
            return
        
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    
    if not user:
        await callback.answer("User not found", show_alert=True)
        return
    
    if user.role == UserRole.ADMIN and delete_type == "other":
        await callback.answer("Admins cannot delete other admins", show_alert=True)
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
        
        if not admin or admin.role != UserRole.ADMIN:
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
