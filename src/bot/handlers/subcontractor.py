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
from src.bot.utils.keyboards import get_job_actions_keyboard, get_decline_reason_keyboard, get_back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

class QuoteStates(StatesGroup):
    waiting_for_quote = State()

class DeclineStates(StatesGroup):
    waiting_for_reason = State()

@router.message(Command("jobs"))
@require_role(UserRole.SUBCONTRACTOR)
async def cmd_jobs(message: Message):
    await show_assigned_jobs(message)

@router.message(F.text == "📋 My Assigned Jobs")
async def btn_assigned_jobs(message: Message):
    if not async_session:
        await message.answer("⚠️ Database not available.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != UserRole.SUBCONTRACTOR:
            await message.answer("❌ You don't have permission to view these jobs.")
            return
    
    await show_assigned_jobs(message)

async def show_assigned_jobs(message: Message):
    jobs = await JobService.get_pending_jobs_for_subcontractor(message.from_user.id)
    
    if not jobs:
        await message.answer(
            "📋 *My Assigned Jobs*\n\n"
            "You have no pending jobs at the moment.\n\n"
            "New jobs will appear here when supervisors assign them to you.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        f"📋 *My Assigned Jobs*\n\n"
        f"You have *{len(jobs)}* pending job(s).\n"
        "Tap on a job to view details and respond:",
        parse_mode="Markdown"
    )
    
    for job in jobs:
        job_type_text = "💰 Quote Required" if job.job_type == JobType.QUOTE else f"🏷️ Price: {job.preset_price or 'N/A'}"
        
        job_text = (
            f"━━━━━━━━━━━━━━━\n"
            f"📋 *Job #{job.id}*\n\n"
            f"*Title:* {job.title}\n"
            f"*Type:* {job_type_text}\n"
        )
        
        if job.description:
            job_text += f"*Description:* {job.description}\n"
        if job.address:
            job_text += f"📍 *Address:* {job.address}\n"
        
        keyboard = get_job_actions_keyboard(job.id, job.job_type.value)
        
        await message.answer(job_text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("job_accept:"))
async def accept_job_callback(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    
    jobs = await JobService.get_pending_jobs_for_subcontractor(callback.from_user.id)
    job = next((j for j in jobs if j.id == job_id), None)
    
    if not job:
        await callback.answer("Job not found or already processed", show_alert=True)
        return
    
    if job.job_type == JobType.QUOTE:
        await state.update_data(accepting_job_id=job_id)
        await callback.message.edit_text(
            f"💬 *Submit Quote for Job #{job_id}*\n\n"
            f"*{job.title}*\n\n"
            "Please enter your quote price:",
            parse_mode="Markdown"
        )
        await state.set_state(QuoteStates.waiting_for_quote)
        await callback.answer()
        return
    
    success, msg = await JobService.accept_job(job_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"✅ *Job Accepted!*\n\n"
            f"Job #{job_id}: {job.title}\n\n"
            "The supervisor has been notified.",
            parse_mode="Markdown"
        )
        await callback.answer("Job accepted! ✅")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("job_quote:"))
async def quote_job_callback(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    
    jobs = await JobService.get_pending_jobs_for_subcontractor(callback.from_user.id)
    job = next((j for j in jobs if j.id == job_id), None)
    
    if not job:
        await callback.answer("Job not found or already processed", show_alert=True)
        return
    
    await state.update_data(accepting_job_id=job_id)
    await callback.message.edit_text(
        f"💬 *Submit Quote for Job #{job_id}*\n\n"
        f"*{job.title}*\n\n"
        "Please enter your quote price\n"
        "(e.g., $500, $1,200):",
        parse_mode="Markdown"
    )
    await state.set_state(QuoteStates.waiting_for_quote)
    await callback.answer()

@router.message(StateFilter(QuoteStates.waiting_for_quote))
async def process_quote(message: Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("❌ Quote submission cancelled.")
        return
    
    data = await state.get_data()
    job_id = data.get('accepting_job_id')
    
    if not job_id:
        await state.clear()
        await message.answer("⚠️ Session expired. Please try again from your job list.")
        return
    
    quoted_price = message.text.strip()
    success, msg = await JobService.accept_job(job_id, message.from_user.id, quoted_price)
    
    if success:
        await message.answer(
            f"✅ *Job Accepted with Quote!*\n\n"
            f"Job #{job_id}\n"
            f"Your Quote: {quoted_price}\n\n"
            "The supervisor has been notified.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"❌ {msg}")
    
    await state.clear()

@router.callback_query(F.data.startswith("job_decline:"))
async def decline_job_callback(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    
    jobs = await JobService.get_pending_jobs_for_subcontractor(callback.from_user.id)
    job = next((j for j in jobs if j.id == job_id), None)
    
    if not job:
        await callback.answer("Job not found or already processed", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"❌ *Decline Job #{job_id}*\n\n"
        f"*{job.title}*\n\n"
        "Please select a reason:",
        reply_markup=get_decline_reason_keyboard(job_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("decline_reason:"))
async def process_decline_reason(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    job_id = int(parts[1])
    reason_type = parts[2]
    
    reason_map = {
        "schedule": "Scheduling conflict",
        "location": "Location too far",
        "busy": "Currently too busy"
    }
    
    if reason_type == "custom":
        await state.update_data(declining_job_id=job_id)
        await callback.message.edit_text(
            f"❌ *Decline Job #{job_id}*\n\n"
            "Please type your reason for declining:",
            parse_mode="Markdown"
        )
        await state.set_state(DeclineStates.waiting_for_reason)
        await callback.answer()
        return
    
    reason = reason_map.get(reason_type, "No reason provided")
    success, msg = await JobService.decline_job(job_id, callback.from_user.id, reason)
    
    if success:
        await callback.message.edit_text(
            f"❌ *Job Declined*\n\n"
            f"Job #{job_id} has been declined.\n"
            f"Reason: {reason}\n\n"
            "The supervisor has been notified.",
            parse_mode="Markdown"
        )
        await callback.answer("Job declined")
    else:
        await callback.answer(msg, show_alert=True)

@router.message(StateFilter(DeclineStates.waiting_for_reason))
async def process_custom_decline_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    job_id = data.get('declining_job_id')
    
    if not job_id:
        await state.clear()
        await message.answer("⚠️ Session expired. Please try again.")
        return
    
    reason = message.text.strip()
    success, msg = await JobService.decline_job(job_id, message.from_user.id, reason)
    
    if success:
        await message.answer(
            f"❌ *Job Declined*\n\n"
            f"Job #{job_id} has been declined.\n"
            f"Reason: {reason}\n\n"
            "The supervisor has been notified.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"❌ {msg}")
    
    await state.clear()

@router.callback_query(F.data.startswith("view_job:sub:"))
async def view_job_subcontractor(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[2])
    
    jobs = await JobService.get_pending_jobs_for_subcontractor(callback.from_user.id)
    job = next((j for j in jobs if j.id == job_id), None)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    job_type_text = "💰 Quote Required" if job.job_type == JobType.QUOTE else f"🏷️ Price: {job.preset_price or 'N/A'}"
    
    job_text = (
        f"📋 *Job #{job.id}*\n\n"
        f"*Title:* {job.title}\n"
        f"*Type:* {job_type_text}\n"
    )
    
    if job.description:
        job_text += f"*Description:* {job.description}\n"
    if job.address:
        job_text += f"📍 *Address:* {job.address}\n"
    
    keyboard = get_job_actions_keyboard(job.id, job.job_type.value)
    
    await callback.message.edit_text(job_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(Command("accept"))
@require_role(UserRole.SUBCONTRACTOR)
async def cmd_accept(message: Message, state: FSMContext):
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer(
            "ℹ️ *Usage:* `/accept <job_id>`\n\n"
            "Or use the buttons in your job list (📋 My Assigned Jobs)",
            parse_mode="Markdown"
        )
        return
    
    try:
        job_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Invalid job ID.")
        return
    
    quoted_price = parts[2] if len(parts) > 2 else None
    success, msg = await JobService.accept_job(job_id, message.from_user.id, quoted_price)
    
    if success:
        await message.answer(f"✅ {msg}")
    else:
        await message.answer(f"❌ {msg}")

@router.message(Command("decline"))
@require_role(UserRole.SUBCONTRACTOR)
async def cmd_decline(message: Message):
    parts = message.text.split(maxsplit=2)
    
    if len(parts) < 2:
        await message.answer(
            "ℹ️ *Usage:* `/decline <job_id> [reason]`\n\n"
            "Or use the buttons in your job list (📋 My Assigned Jobs)",
            parse_mode="Markdown"
        )
        return
    
    try:
        job_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Invalid job ID.")
        return
    
    reason = parts[2] if len(parts) > 2 else None
    success, msg = await JobService.decline_job(job_id, message.from_user.id, reason)
    
    if success:
        await message.answer(f"✅ {msg}")
    else:
        await message.answer(f"❌ {msg}")
