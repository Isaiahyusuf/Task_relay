from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from src.bot.database import async_session, User, Job
from src.bot.database.models import UserRole, JobType, JobStatus, AvailabilityStatus
from src.bot.services.jobs import JobService
from src.bot.services.quotes import QuoteService
from src.bot.services.availability import AvailabilityService
from src.bot.utils.permissions import require_role
from src.bot.utils.keyboards import (
    get_job_actions_keyboard, get_decline_reason_keyboard, get_back_keyboard,
    get_job_list_keyboard
)
import logging

logger = logging.getLogger(__name__)
router = Router()

class QuoteStates(StatesGroup):
    waiting_for_quote = State()
    waiting_for_notes = State()

class DeclineStates(StatesGroup):
    waiting_for_reason = State()

class CompletionStates(StatesGroup):
    waiting_for_photo = State()

class SubmissionStates(StatesGroup):
    waiting_for_notes = State()
    waiting_for_photo = State()

class AcceptJobStates(StatesGroup):
    waiting_for_company_name = State()

@router.message(F.text == "📋 Available Jobs")
async def btn_available_jobs(message: Message):
    if not await check_subcontractor(message):
        return
    await show_available_jobs(message)

@router.message(F.text == "🔄 My Active Jobs")
async def btn_active_jobs(message: Message):
    if not await check_subcontractor(message):
        return
    await show_active_jobs(message)

@router.message(F.text == "🟢 Available")
async def btn_set_available(message: Message):
    if not await check_subcontractor(message):
        return
    success, msg = await AvailabilityService.set_availability(
        message.from_user.id, AvailabilityStatus.AVAILABLE
    )
    await message.answer(f"🟢 {msg}" if success else f"Error: {msg}")

@router.message(F.text == "🟡 Busy")
async def btn_set_busy(message: Message):
    if not await check_subcontractor(message):
        return
    success, msg = await AvailabilityService.set_availability(
        message.from_user.id, AvailabilityStatus.BUSY
    )
    await message.answer(f"🟡 {msg}" if success else f"Error: {msg}")

@router.message(F.text == "🔴 Away")
async def btn_set_away(message: Message):
    if not await check_subcontractor(message):
        return
    success, msg = await AvailabilityService.set_availability(
        message.from_user.id, AvailabilityStatus.AWAY
    )
    await message.answer(f"🔴 {msg}" if success else f"Error: {msg}")

async def check_subcontractor(message: Message) -> bool:
    if not async_session:
        await message.answer("Database not available.")
        return False
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != UserRole.SUBCONTRACTOR:
            await message.answer("You don't have permission for this action.")
            return False
    return True

async def show_available_jobs(message: Message):
    jobs = await JobService.get_pending_jobs_for_subcontractor(message.from_user.id)
    
    if not jobs:
        await message.answer(
            "*Available Jobs*\n\n"
            "No jobs available at the moment.\n\n"
            "New jobs will appear here when supervisors send them.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        f"*Available Jobs*\n\n"
        f"You have *{len(jobs)}* available job(s).\n"
        "Tap on a job to view details and respond:",
        parse_mode="Markdown"
    )
    
    for job in jobs[:5]:
        job_type_text = "Quote Required" if job.job_type == JobType.QUOTE else f"Price: {job.preset_price or 'N/A'}"
        
        job_text = (
            f"*Job #{job.id}*\n\n"
            f"*Title:* {job.title}\n"
            f"*Type:* {job_type_text}\n"
        )
        
        if job.description:
            job_text += f"*Description:* {job.description}\n"
        if job.address:
            job_text += f"*Address:* {job.address}\n"
        
        keyboard = get_job_actions_keyboard(job.id, job.job_type.value, "sent")
        
        await message.answer(job_text, reply_markup=keyboard, parse_mode="Markdown")

async def show_active_jobs(message: Message):
    jobs = await JobService.get_subcontractor_active_jobs(message.from_user.id)
    
    if not jobs:
        await message.answer(
            "*My Active Jobs*\n\n"
            "You have no active jobs at the moment.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        f"*My Active Jobs*\n\n"
        f"You have *{len(jobs)}* active job(s):",
        parse_mode="Markdown"
    )
    
    for job in jobs:
        status_text = "Accepted" if job.status == JobStatus.ACCEPTED else "In Progress"
        job_type_text = "Quote" if job.job_type == JobType.QUOTE else f"Price: {job.preset_price or 'N/A'}"
        
        job_text = (
            f"*Job #{job.id}* - {status_text}\n\n"
            f"*Title:* {job.title}\n"
            f"*Type:* {job_type_text}\n"
        )
        
        if job.address:
            job_text += f"*Address:* {job.address}\n"
        
        keyboard = get_job_actions_keyboard(job.id, job.job_type.value, job.status.value)
        
        await message.answer(job_text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("job_accept:"))
async def accept_job_callback(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    
    job = await JobService.get_job_by_id(job_id)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    if job.job_type == JobType.QUOTE:
        await callback.answer("Quote jobs require a quote submission first", show_alert=True)
        return
    
    # Ask for company name before accepting
    await state.update_data(accepting_job_id=job_id, job_title=job.title)
    await callback.message.edit_text(
        f"*Accept Job #{job_id}*\n\n"
        f"*{job.title}*\n\n"
        "Please enter your company name to accept this job:",
        parse_mode="Markdown"
    )
    await state.set_state(AcceptJobStates.waiting_for_company_name)
    await callback.answer()

@router.message(StateFilter(AcceptJobStates.waiting_for_company_name))
async def process_company_name_for_accept(message: Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Job acceptance cancelled.")
        return
    
    company_name = message.text.strip()
    
    if len(company_name) < 2:
        await message.answer("Please enter a valid company name (at least 2 characters) or /cancel:")
        return
    
    data = await state.get_data()
    job_id = data.get('accepting_job_id')
    job_title = data.get('job_title')
    
    success, msg, supervisor_tg_id = await JobService.accept_job(job_id, message.from_user.id, company_name)
    
    if success:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user_obj = result.scalar_one_or_none()
            sub_name = user_obj.first_name or user_obj.username or "A subcontractor"

        await message.answer(
            f"*Job Accepted!*\n\n"
            f"Job #{job_id}: {job_title}\n"
            f"Company: {company_name}\n\n"
            "Use 'My Active Jobs' to start the job when ready.",
            parse_mode="Markdown"
        )
        
        # Notify Supervisor
        if supervisor_tg_id:
            bot = message.bot
            if bot:
                try:
                    await bot.send_message(
                        supervisor_tg_id,
                        f"✅ *Job Accepted*\n\n"
                        f"Job #{job_id} ({job_title}) has been accepted by *{sub_name}*.\n"
                        f"Company: *{company_name}*",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify supervisor {supervisor_tg_id}: {e}")
            else:
                logger.error("Bot instance is None, cannot notify supervisor")
    else:
        await message.answer(f"Error: {msg}")
    
    await state.clear()

@router.callback_query(F.data.startswith("job_done:"))
async def mark_job_done_callback(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    job = await JobService.get_job_by_id(job_id)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return

    # Check if job is already marked as done
    if job.status == JobStatus.COMPLETED:
        await callback.answer("Job already marked as done", show_alert=True)
        return

    success, msg = await JobService.complete_job(job_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"*Job Marked as Done!*\n\n"
            f"Job #{job_id}: {job.title}\n\n"
            "The supervisor has been notified for investigation.",
            parse_mode="Markdown"
        )
        await callback.answer("Job marked as done!")
        
        # Notify Supervisor
        async with async_session() as session:
            sup_result = await session.execute(
                select(User.telegram_id).where(User.id == job.supervisor_id)
            )
            supervisor_tg_id = sup_result.scalar()
            
            sub_result = await session.execute(
                select(User).where(User.telegram_id == callback.from_user.id)
            )
            sub = sub_result.scalar_one_or_none()
            sub_name = sub.first_name or sub.username or "A subcontractor"

        if supervisor_tg_id:
            bot = callback.bot
            if bot:
                try:
                    await bot.send_message(
                        supervisor_tg_id,
                        f"🔔 *Job Marked Done*\n\n"
                        f"Job #{job_id} ({job.title}) has been marked as done by *{sub_name}*.\n\n"
                        f"Please investigate and mark as completed if satisfied.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify supervisor {supervisor_tg_id}: {e}")
            else:
                logger.error("Bot instance is None, cannot notify supervisor")
    else:
        await callback.answer(msg, show_alert=True)

@router.message(F.text == "📤 Submit Job")
async def btn_submit_job_menu(message: Message):
    if not await check_subcontractor(message):
        return
    
    jobs = await JobService.get_subcontractor_active_jobs(message.from_user.id)
    in_progress_jobs = [j for j in jobs if j.status == JobStatus.IN_PROGRESS]
    
    if not in_progress_jobs:
        await message.answer(
            "*Submit Job*\n\n"
            "You have no jobs in progress to submit.\n\n"
            "Start a job first from 'My Active Jobs'.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        "*Submit Job*\n\n"
        "Select a job to submit for supervisor review:",
        reply_markup=get_job_list_keyboard(in_progress_jobs, context="submit"),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("view_job:submit:"))
async def view_job_for_submission(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[2])
    await start_job_submission(callback, state, job_id)

@router.callback_query(F.data.startswith("job_submit:"))
async def submit_job_callback(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    await start_job_submission(callback, state, job_id)

async def start_job_submission(callback: CallbackQuery, state: FSMContext, job_id: int):
    job = await JobService.get_job_by_id(job_id)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    await state.update_data(submitting_job_id=job_id, job_title=job.title)
    await callback.message.edit_text(
        f"*Submit Job #{job_id}*\n\n"
        f"*{job.title}*\n\n"
        "Please provide any notes about the completed work\n"
        "(or send /skip to continue without notes):",
        parse_mode="Markdown"
    )
    await state.set_state(SubmissionStates.waiting_for_notes)
    await callback.answer()

@router.message(StateFilter(SubmissionStates.waiting_for_notes))
async def process_submission_notes(message: Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Job submission cancelled.")
        return
    
    notes = None if message.text.strip().lower() == "/skip" else message.text.strip()
    await state.update_data(submission_notes=notes, submission_photos=[])
    
    await message.answer(
        "*Submit Job*\n\n"
        "Now please send photos as proof of completed work.\n"
        "You can send multiple photos. When done, type /done to submit.",
        parse_mode="Markdown"
    )
    await state.set_state(SubmissionStates.waiting_for_photo)

@router.message(StateFilter(SubmissionStates.waiting_for_photo), F.text == "/done")
async def finish_photo_submission(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('submission_photos', [])
    
    if not photos:
        await message.answer(
            "You must include at least one photo to submit the job.\n"
            "Please send a photo first."
        )
        return
    
    job_id = data.get('submitting_job_id')
    notes = data.get('submission_notes')
    photos_str = ",".join(photos)
    
    success, msg, supervisor_tg_id = await JobService.submit_job(
        job_id, message.from_user.id, notes, photos_str
    )
    
    if success:
        await state.clear()
        await message.answer(
            f"*Job Submitted!*\n\n"
            f"Job #{job_id} has been submitted with {len(photos)} photo(s) for supervisor review.\n\n"
            "The supervisor will be notified to investigate and mark as completed.",
            parse_mode="Markdown"
        )
        
        # Send notification to supervisor with photos
        logger.info(f"Attempting to notify supervisor. supervisor_tg_id={supervisor_tg_id}")
        
        if supervisor_tg_id:
            from aiogram.types import InputMediaPhoto
            bot = message.bot
            
            if not bot:
                logger.error("Bot instance is None, cannot notify supervisor")
            else:
                async with async_session() as session:
                    result = await session.execute(
                        select(User).where(User.telegram_id == message.from_user.id)
                    )
                    sub = result.scalar_one_or_none()
                    sub_name = sub.first_name or sub.username or "A subcontractor" if sub else "A subcontractor"
                    company_name = ""
                    job_obj = await JobService.get_job_by_id(job_id)
                    if job_obj and job_obj.company_name:
                        company_name = f"\nCompany: {job_obj.company_name}"
                
                try:
                    job = await JobService.get_job_by_id(job_id)
                    notes_text = f"\nNotes: {notes}" if notes else ""
                    
                    logger.info(f"Sending notification message to supervisor {supervisor_tg_id}")
                    await bot.send_message(
                        supervisor_tg_id,
                        f"📋 *Job Submitted for Review*\n\n"
                        f"Job #{job_id}: {job.title if job else 'Unknown'}\n"
                        f"Submitted by: *{sub_name}*{company_name}{notes_text}\n\n"
                        f"📸 Photos ({len(photos)}) attached below.\n"
                        f"Please review and mark as completed if satisfied.",
                        parse_mode="Markdown"
                    )
                    
                    logger.info(f"Sending {len(photos)} photos to supervisor {supervisor_tg_id}")
                    if photos:
                        if len(photos) == 1:
                            await bot.send_photo(supervisor_tg_id, photos[0])
                        else:
                            media_group = [InputMediaPhoto(media=photo_id) for photo_id in photos]
                            await bot.send_media_group(supervisor_tg_id, media_group)
                    
                    logger.info(f"Successfully notified supervisor {supervisor_tg_id} with photos")
                            
                except Exception as e:
                    logger.error(f"Failed to notify supervisor {supervisor_tg_id}: {e}", exc_info=True)
        else:
            logger.warning(f"No supervisor_tg_id returned for job {job_id}, cannot send notification")
    else:
        await message.answer(f"Error: {msg}")

@router.message(StateFilter(SubmissionStates.waiting_for_photo))
async def process_submission_photo(message: Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Job submission cancelled.")
        return
    
    if not message.photo:
        await message.answer(
            "Please send a photo as proof of completed work.\n"
            "Type /done when finished or /cancel to cancel."
        )
        return
    
    photo = message.photo[-1]
    data = await state.get_data()
    photos = data.get('submission_photos', [])
    photos.append(photo.file_id)
    await state.update_data(submission_photos=photos)
    
    await message.answer(
        f"Photo {len(photos)} added.\n\n"
        f"Send more photos or type /done to submit the job."
    )

@router.callback_query(F.data.startswith("job_quote:"))
async def quote_job_callback(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    
    job = await JobService.get_job_by_id(job_id)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    await state.update_data(quoting_job_id=job_id, job_title=job.title)
    await callback.message.edit_text(
        f"*Submit Quote for Job #{job_id}*\n\n"
        f"*{job.title}*\n\n"
        "Please enter your quote amount\n"
        "(e.g., $500, $1,200):",
        parse_mode="Markdown"
    )
    await state.set_state(QuoteStates.waiting_for_quote)
    await callback.answer()

@router.message(StateFilter(QuoteStates.waiting_for_quote))
async def process_quote_amount(message: Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Quote submission cancelled.")
        return
    
    await state.update_data(quote_amount=message.text.strip())
    await message.answer(
        "Would you like to add any notes to your quote?\n\n"
        "Type your notes or send /skip to submit without notes:"
    )
    await state.set_state(QuoteStates.waiting_for_notes)

@router.message(StateFilter(QuoteStates.waiting_for_notes))
async def process_quote_notes(message: Message, state: FSMContext):
    data = await state.get_data()
    job_id = data.get('quoting_job_id')
    amount = data.get('quote_amount')
    
    notes = None if message.text.strip().lower() == "/skip" else message.text.strip()
    
    success, msg = await QuoteService.submit_quote(job_id, message.from_user.id, amount, notes)
    
    if success:
        await message.answer(
            f"*Quote Submitted!*\n\n"
            f"Job #{job_id}\n"
            f"Your Quote: {amount}\n\n"
            "The supervisor will review your quote and notify you if accepted.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"Error: {msg}")
    
    await state.clear()

@router.callback_query(F.data.startswith("job_start:"))
async def start_job_callback(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    success, msg = await JobService.start_job(job_id, callback.from_user.id)
    
    if success:
        job = await JobService.get_job_by_id(job_id)
        await callback.message.edit_text(
            f"*Job Started!*\n\n"
            f"Job #{job_id}: {job.title if job else 'Unknown'}\n\n"
            "You can mark the job as complete when finished.",
            reply_markup=get_job_actions_keyboard(job_id, "preset", "in_progress"),
            parse_mode="Markdown"
        )
        await callback.answer("Job started!")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("job_complete:"))
async def complete_job_callback(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    
    await state.update_data(completing_job_id=job_id)
    await callback.message.edit_text(
        f"*Completing Job #{job_id}*\n\n"
        "Please send a photo of the completed work as evidence:",
        parse_mode="Markdown"
    )
    await state.set_state(CompletionStates.waiting_for_photo)
    await callback.answer()

@router.message(StateFilter(CompletionStates.waiting_for_photo), F.photo)
async def process_completion_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    job_id = data.get('completing_job_id')
    photo = message.photo[-1]
    
    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.photos = photo.file_id
            await session.commit()

    success, msg = await JobService.complete_job(job_id, message.from_user.id)
    
    if success:
        await message.answer(
            f"*Job Completed!*\n\n"
            f"Job #{job_id} has been marked as complete with photo evidence.\n\n"
            "Great work!",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"Error: {msg}")
    
    await state.clear()

@router.callback_query(F.data.startswith("job_decline:"))
async def decline_job_callback(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    job = await JobService.get_job_by_id(job_id)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"*Decline Job #{job_id}*\n\n"
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
            f"*Decline Job #{job_id}*\n\n"
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
            f"*Job Declined*\n\n"
            f"Job #{job_id} has been declined.\n"
            f"Reason: {reason}",
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
        await message.answer("Session expired. Please try again.")
        return
    
    reason = message.text.strip()
    success, msg = await JobService.decline_job(job_id, message.from_user.id, reason)
    
    if success:
        await message.answer(
            f"*Job Declined*\n\n"
            f"Job #{job_id} has been declined.\n"
            f"Reason: {reason}",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"Error: {msg}")
    
    await state.clear()
