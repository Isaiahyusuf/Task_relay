from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from src.bot.database import async_session, User, Job
from src.bot.database.models import UserRole, JobType, JobStatus
from src.bot.services.jobs import JobService
from src.bot.utils.permissions import require_role
from src.bot.utils.keyboards import (
    get_job_type_keyboard, get_skip_keyboard, get_subcontractor_selection_keyboard,
    get_confirmation_keyboard, get_job_list_keyboard, get_main_menu_keyboard, get_back_keyboard
)
import logging

logger = logging.getLogger(__name__)
router = Router()

class NewJobStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_type = State()
    waiting_for_description = State()
    waiting_for_address = State()
    waiting_for_price = State()
    waiting_for_subcontractor = State()
    confirming = State()

@router.message(Command("newjob"))
@require_role(UserRole.SUPERVISOR)
async def cmd_new_job(message: Message, state: FSMContext):
    await start_new_job(message, state)

@router.message(F.text == "➕ New Job")
async def btn_new_job(message: Message, state: FSMContext):
    if not async_session:
        await message.answer("⚠️ Database not available.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != UserRole.SUPERVISOR:
            await message.answer("❌ You don't have permission to create jobs.")
            return
    
    await start_new_job(message, state)

async def start_new_job(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📝 *Creating a New Job*\n\n"
        "Step 1/5: Please enter the job title:",
        parse_mode="Markdown"
    )
    await state.set_state(NewJobStates.waiting_for_title)

@router.message(StateFilter(NewJobStates.waiting_for_title))
async def process_job_title(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("❌ Job creation cancelled.")
        await state.clear()
        return
    
    await state.update_data(title=message.text.strip())
    
    await message.answer(
        "📝 *Creating a New Job*\n\n"
        "Step 2/5: Select the job type:",
        reply_markup=get_job_type_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(NewJobStates.waiting_for_type)

@router.callback_query(F.data == "job_cancel")
async def cancel_job_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Job creation cancelled.")
    await callback.answer()

@router.callback_query(F.data.startswith("job_type:"), StateFilter(NewJobStates.waiting_for_type))
async def process_job_type(callback: CallbackQuery, state: FSMContext):
    job_type_str = callback.data.split(":")[1]
    job_type = JobType.QUOTE if job_type_str == "quote" else JobType.PRESET_PRICE
    await state.update_data(job_type=job_type)
    
    type_name = "Quote Job 💰" if job_type == JobType.QUOTE else "Preset Price Job 🏷️"
    
    await callback.message.edit_text(
        f"📝 *Creating a New Job*\n\n"
        f"Type: {type_name}\n\n"
        "Step 3/5: Enter job description\n"
        "(or tap Skip to continue without):",
        reply_markup=get_skip_keyboard("description"),
        parse_mode="Markdown"
    )
    await state.set_state(NewJobStates.waiting_for_description)
    await callback.answer()

@router.callback_query(F.data == "skip:description", StateFilter(NewJobStates.waiting_for_description))
async def skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description=None)
    await ask_for_address(callback.message, state, edit=True)
    await callback.answer()

@router.message(StateFilter(NewJobStates.waiting_for_description))
async def process_job_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await ask_for_address(message, state, edit=False)

async def ask_for_address(message: Message, state: FSMContext, edit: bool = False):
    text = (
        "📝 *Creating a New Job*\n\n"
        "Step 4/5: Enter the job address/location\n"
        "(or tap Skip to continue without):"
    )
    keyboard = get_skip_keyboard("address")
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.set_state(NewJobStates.waiting_for_address)

@router.callback_query(F.data == "skip:address", StateFilter(NewJobStates.waiting_for_address))
async def skip_address(callback: CallbackQuery, state: FSMContext):
    await state.update_data(address=None)
    data = await state.get_data()
    
    if data['job_type'] == JobType.PRESET_PRICE:
        await ask_for_price(callback.message, state, edit=True)
    else:
        await show_subcontractor_selection(callback.message, state, callback.from_user.id, edit=True)
    await callback.answer()

@router.message(StateFilter(NewJobStates.waiting_for_address))
async def process_job_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    data = await state.get_data()
    
    if data['job_type'] == JobType.PRESET_PRICE:
        await ask_for_price(message, state, edit=False)
    else:
        await show_subcontractor_selection(message, state, message.from_user.id, edit=False)

async def ask_for_price(message: Message, state: FSMContext, edit: bool = False):
    text = (
        "📝 *Creating a New Job*\n\n"
        "Step 5/5: Enter the preset price\n"
        "(e.g., $500, $1,200):"
    )
    
    if edit:
        await message.edit_text(text, parse_mode="Markdown")
    else:
        await message.answer(text, parse_mode="Markdown")
    
    await state.set_state(NewJobStates.waiting_for_price)

@router.message(StateFilter(NewJobStates.waiting_for_price))
async def process_job_price(message: Message, state: FSMContext):
    await state.update_data(preset_price=message.text.strip())
    await show_subcontractor_selection(message, state, message.from_user.id, edit=False)

async def show_subcontractor_selection(message: Message, state: FSMContext, telegram_id: int, edit: bool = False):
    if not async_session:
        await message.answer("⚠️ Database error. Please try again.")
        await state.clear()
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        supervisor = result.scalar_one_or_none()
        
        subcontractors_result = await session.execute(
            select(User).where(
                User.role == UserRole.SUBCONTRACTOR,
                User.team_id == supervisor.team_id,
                User.is_active == True
            )
        )
        subcontractors = list(subcontractors_result.scalars().all())
    
    await state.update_data(supervisor_id=supervisor.id, team_id=supervisor.team_id)
    
    if not subcontractors:
        text = (
            "📝 *Creating a New Job*\n\n"
            "⚠️ No subcontractors available in your team.\n\n"
            "Would you like to save the job as pending?"
        )
        keyboard = get_confirmation_keyboard("save_pending")
    else:
        text = (
            "📝 *Creating a New Job*\n\n"
            "Final step: Select a subcontractor to dispatch the job to:"
        )
        keyboard = get_subcontractor_selection_keyboard(subcontractors)
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.set_state(NewJobStates.waiting_for_subcontractor)

@router.callback_query(F.data.startswith("assign:"), StateFilter(NewJobStates.waiting_for_subcontractor))
async def process_subcontractor_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    job = await JobService.create_job(
        supervisor_id=data['supervisor_id'],
        title=data['title'],
        job_type=data['job_type'],
        description=data.get('description'),
        address=data.get('address'),
        preset_price=data.get('preset_price'),
        team_id=data.get('team_id')
    )
    
    if not job:
        await callback.message.edit_text("❌ Failed to create job. Please try again.")
        await state.clear()
        await callback.answer()
        return
    
    subcontractor_part = callback.data.split(":")[1]
    
    if subcontractor_part == "none":
        await callback.message.edit_text(
            f"✅ *Job Created Successfully!*\n\n"
            f"📋 Job #{job.id}: {job.title}\n"
            f"📌 Status: Pending (not dispatched)\n\n"
            "You can dispatch it later from 'My Jobs'.",
            parse_mode="Markdown"
        )
    else:
        subcontractor_id = int(subcontractor_part)
        success = await JobService.dispatch_job(job.id, subcontractor_id)
        
        if success:
            await callback.message.edit_text(
                f"✅ *Job Created & Dispatched!*\n\n"
                f"📋 Job #{job.id}: {job.title}\n"
                f"📌 Status: Dispatched to subcontractor\n\n"
                "The subcontractor will be notified.",
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                f"⚠️ Job #{job.id} created but dispatch failed.\n"
                "Please try dispatching again from 'My Jobs'."
            )
    
    await state.clear()
    await callback.answer("Job created! ✅")

@router.callback_query(F.data.startswith("confirm:save_pending"))
async def confirm_save_pending(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    job = await JobService.create_job(
        supervisor_id=data['supervisor_id'],
        title=data['title'],
        job_type=data['job_type'],
        description=data.get('description'),
        address=data.get('address'),
        preset_price=data.get('preset_price'),
        team_id=data.get('team_id')
    )
    
    if job:
        await callback.message.edit_text(
            f"✅ *Job Saved!*\n\n"
            f"📋 Job #{job.id}: {job.title}\n"
            f"📌 Status: Pending\n\n"
            "You can dispatch it later when subcontractors are available.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text("❌ Failed to create job.")
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("cancel:save_pending"))
async def cancel_save_pending(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Job creation cancelled.")
    await callback.answer()

@router.message(Command("myjobs"))
@require_role(UserRole.SUPERVISOR)
async def cmd_my_jobs(message: Message):
    await show_my_jobs(message)

@router.message(F.text == "📋 My Jobs")
async def btn_my_jobs(message: Message):
    if not async_session:
        await message.answer("⚠️ Database not available.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != UserRole.SUPERVISOR:
            await message.answer("❌ You don't have permission to view jobs.")
            return
    
    await show_my_jobs(message)

async def show_my_jobs(message: Message):
    if not async_session:
        await message.answer("⚠️ Database error.")
        return
    
    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        jobs_result = await session.execute(
            select(Job).where(
                Job.supervisor_id == user.id,
                Job.status != JobStatus.ARCHIVED
            ).order_by(Job.created_at.desc()).limit(20)
        )
        jobs = list(jobs_result.scalars().all())
    
    if not jobs:
        await message.answer(
            "📋 *My Jobs*\n\n"
            "You haven't created any jobs yet.\n\n"
            "Tap '➕ New Job' to create one!",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        "📋 *My Jobs*\n\n"
        "Select a job to view details:",
        reply_markup=get_job_list_keyboard(jobs, context="sup"),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("view_job:sup:"))
async def view_job_details_supervisor(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[2])
    
    if not async_session:
        await callback.answer("Database error", show_alert=True)
        return
    
    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    status_emoji = {
        JobStatus.PENDING: "⏳ Pending",
        JobStatus.DISPATCHED: "📤 Dispatched",
        JobStatus.ACCEPTED: "✅ Accepted",
        JobStatus.DECLINED: "❌ Declined",
        JobStatus.COMPLETED: "✔️ Completed",
        JobStatus.ARCHIVED: "📦 Archived"
    }.get(job.status, "Unknown")
    
    type_emoji = "💰 Quote" if job.job_type == JobType.QUOTE else "🏷️ Preset Price"
    
    details = (
        f"📋 *Job #{job.id}*\n\n"
        f"*Title:* {job.title}\n"
        f"*Type:* {type_emoji}\n"
        f"*Status:* {status_emoji}\n"
    )
    
    if job.description:
        details += f"*Description:* {job.description}\n"
    if job.address:
        details += f"*Address:* {job.address}\n"
    if job.preset_price:
        details += f"*Price:* {job.preset_price}\n"
    if job.quoted_price:
        details += f"*Quoted:* {job.quoted_price}\n"
    if job.decline_reason:
        details += f"*Decline Reason:* {job.decline_reason}\n"
    
    details += f"\n*Created:* {job.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    await callback.message.edit_text(
        details,
        reply_markup=get_back_keyboard("back:sup"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back:sup")
async def back_to_my_jobs(callback: CallbackQuery):
    if not async_session:
        await callback.answer("Database error", show_alert=True)
        return
    
    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        jobs_result = await session.execute(
            select(Job).where(
                Job.supervisor_id == user.id,
                Job.status != JobStatus.ARCHIVED
            ).order_by(Job.created_at.desc()).limit(20)
        )
        jobs = list(jobs_result.scalars().all())
    
    await callback.message.edit_text(
        "📋 *My Jobs*\n\n"
        "Select a job to view details:",
        reply_markup=get_job_list_keyboard(jobs, context="sup"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("page:sup:"))
async def handle_supervisor_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[2])
    
    if not async_session:
        await callback.answer("Database error", show_alert=True)
        return
    
    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        jobs_result = await session.execute(
            select(Job).where(
                Job.supervisor_id == user.id,
                Job.status != JobStatus.ARCHIVED
            ).order_by(Job.created_at.desc()).limit(50)
        )
        jobs = list(jobs_result.scalars().all())
    
    await callback.message.edit_reply_markup(
        reply_markup=get_job_list_keyboard(jobs, page=page, context="sup")
    )
    await callback.answer()
