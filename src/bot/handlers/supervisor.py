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
from src.bot.services.access_codes import AccessCodeService
from src.bot.handlers.admin import CreateCodeStates
from src.bot.utils.permissions import require_role
from src.bot.utils.keyboards import (
    get_job_type_keyboard, get_skip_keyboard, get_subcontractor_selection_keyboard,
    get_confirmation_keyboard, get_job_list_keyboard, get_main_menu_keyboard, 
    get_back_keyboard, get_supervisor_job_actions_keyboard, get_quotes_keyboard,
    get_quote_detail_keyboard
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

class RatingStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_comment = State()

@router.message(Command("newjob"))
@require_role(UserRole.SUPERVISOR)
async def cmd_new_job(message: Message, state: FSMContext):
    await start_new_job(message, state)

@router.message(F.text == "🔑 Create Subcontractor Code")
@require_role(UserRole.SUPERVISOR)
async def btn_create_sub_code(message: Message, state: FSMContext):
    await message.answer(
        "*Create Subcontractor Access Code*\n\n"
        "Step 1/2: Enter the access code\n"
        "(letters and numbers only):",
        parse_mode="Markdown"
    )
    await state.set_state(CreateCodeStates.waiting_for_code)
    # Use preset_role instead of forced_role to trigger team selection
    await state.update_data(preset_role=UserRole.SUBCONTRACTOR.value, preset_role_name="Subcontractor")

@router.message(F.text == "➕ New Job")
async def btn_new_job(message: Message, state: FSMContext):
    if not async_session:
        await message.answer("Database not available.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != UserRole.SUPERVISOR:
            await message.answer("You don't have permission to create jobs.")
            return
    
    await start_new_job(message, state)

async def start_new_job(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "*Creating a New Job*\n\n"
        "Step 1/5: Please enter the job title:",
        parse_mode="Markdown"
    )
    await state.set_state(NewJobStates.waiting_for_title)

@router.message(StateFilter(NewJobStates.waiting_for_title))
async def process_job_title(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Job creation cancelled.")
        await state.clear()
        return
    
    await state.update_data(title=message.text.strip())
    
    await message.answer(
        "*Creating a New Job*\n\n"
        "Step 2/5: Select the job type:",
        reply_markup=get_job_type_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(NewJobStates.waiting_for_type)

@router.callback_query(F.data == "job_cancel")
async def cancel_job_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Job creation cancelled.")
    await callback.answer()

@router.callback_query(F.data.startswith("job_type:"), StateFilter(NewJobStates.waiting_for_type))
async def process_job_type(callback: CallbackQuery, state: FSMContext):
    job_type_str = callback.data.split(":")[1]
    job_type = JobType.QUOTE if job_type_str == "quote" else JobType.PRESET_PRICE
    await state.update_data(job_type=job_type)
    
    type_name = "Quote Job" if job_type == JobType.QUOTE else "Preset Price Job"
    
    await callback.message.edit_text(
        f"*Creating a New Job*\n\n"
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
        "*Creating a New Job*\n\n"
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
    if message.text.startswith("/"):
        await message.answer("Job creation cancelled.")
        await state.clear()
        return
        
    await state.update_data(address=message.text.strip())
    data = await state.get_data()
    
    if data['job_type'] == JobType.PRESET_PRICE:
        await ask_for_price(message, state, edit=False)
    else:
        await show_subcontractor_selection(message, state, message.from_user.id, edit=False)

async def ask_for_price(message: Message, state: FSMContext, edit: bool = False):
    text = (
        "*Creating a New Job*\n\n"
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
    if message.text.startswith("/"):
        await message.answer("Job creation cancelled.")
        await state.clear()
        return
        
    await state.update_data(preset_price=message.text.strip())
    await show_team_selection(message, state, message.from_user.id, edit=False)

async def show_team_selection(message: Message, state: FSMContext, telegram_id: int, edit: bool = False):
    if not async_session:
        await message.answer("Database error. Please try again.")
        await state.clear()
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        supervisor = result.scalar_one_or_none()
    
    await state.update_data(supervisor_id=supervisor.id, team_id=supervisor.team_id)
    
    from src.bot.utils.keyboards import get_job_team_selection_keyboard
    text = (
        "*Creating a New Job*\n\n"
        "Final step: Where do you want to send this job?\n\n"
        "🌐 *Bot-Wide* - All available subcontractors\n"
        "🌲 *Northwest* - Northwest Team only\n"
        "☀️ *Southeast* - Southeast Team only"
    )
    keyboard = get_job_team_selection_keyboard()
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.set_state(NewJobStates.waiting_for_subcontractor)

@router.callback_query(F.data.startswith("job_send:"), StateFilter(NewJobStates.waiting_for_subcontractor))
async def process_team_send(callback: CallbackQuery, state: FSMContext):
    from src.bot.database.models import Team, TeamType
    
    data = await state.get_data()
    send_option = callback.data.split(":")[1]
    
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
        await callback.message.edit_text("Failed to create job. Please try again.")
        await state.clear()
        await callback.answer()
        return
    
    if send_option == "draft":
        await callback.message.edit_text(
            f"*Job Saved as Draft!*\n\n"
            f"Job #{job.id}: {job.title}\n"
            f"Status: Created (not sent)\n\n"
            "You can send it later from 'My Jobs'.",
            parse_mode="Markdown"
        )
    else:
        # Send to team(s)
        success, msg = await JobService.send_job_to_all(job.id)
        
        if success:
            # Determine which subcontractors to notify
            async with async_session() as session:
                from sqlalchemy import or_
                
                if send_option == "all":
                    # All available subcontractors (AVAILABLE or NULL status)
                    result = await session.execute(
                        select(User).where(
                            User.role == UserRole.SUBCONTRACTOR,
                            User.is_active == True,
                            or_(
                                User.availability_status == AvailabilityStatus.AVAILABLE,
                                User.availability_status == None
                            )
                        )
                    )
                    team_label = "all teams"
                else:
                    # Get team by type
                    team_type = TeamType.NORTHWEST if send_option == "northwest" else TeamType.SOUTHEAST
                    team_result = await session.execute(
                        select(Team).where(Team.team_type == team_type)
                    )
                    team = team_result.scalar_one_or_none()
                    
                    if team:
                        result = await session.execute(
                            select(User).where(
                                User.role == UserRole.SUBCONTRACTOR,
                                User.is_active == True,
                                or_(
                                    User.availability_status == AvailabilityStatus.AVAILABLE,
                                    User.availability_status == None
                                ),
                                User.team_id == team.id
                            )
                        )
                        team_label = team.name
                    else:
                        result = await session.execute(
                            select(User).where(User.id == -1)  # Empty result
                        )
                        team_label = send_option.title()
                
                available_subs = list(result.scalars().all())
                
                from src.bot.main import bot
                notified_count = 0
                for sub in available_subs:
                    try:
                        await bot.send_message(
                            sub.telegram_id,
                            f"🆕 *New Job Available*\n\n"
                            f"Job #{job.id}: {job.title}\n"
                            f"Location: {job.address or 'N/A'}\n"
                            f"Price: {job.preset_price or 'N/A'}\n\n"
                            f"Check 'Available Jobs' to accept this job!",
                            parse_mode="Markdown"
                        )
                        notified_count += 1
                    except Exception as e:
                        logger.error(f"Failed to notify subcontractor {sub.telegram_id}: {e}")
                
                # Notify super admins, admins, and supervisors only for bot-wide jobs
                if send_option == "all":
                    mgmt_result = await session.execute(
                        select(User).where(
                            User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPERVISOR]),
                            User.is_active == True,
                            User.telegram_id != callback.from_user.id  # Don't notify the creator
                        )
                    )
                    management_users = list(mgmt_result.scalars().all())
                    
                    for mgmt_user in management_users:
                        try:
                            await bot.send_message(
                                mgmt_user.telegram_id,
                                f"📋 *Bot-Wide Job Created*\n\n"
                                f"Job #{job.id}: {job.title}\n"
                                f"Sent to: All Teams\n"
                                f"Location: {job.address or 'N/A'}\n"
                                f"Price: {job.preset_price or 'N/A'}\n\n"
                                f"Created by a supervisor.",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.error(f"Failed to notify management user {mgmt_user.telegram_id}: {e}")
            
            await callback.message.edit_text(
                f"*Job Created & Sent!*\n\n"
                f"Job #{job.id}: {job.title}\n"
                f"Sent to: {team_label}\n\n"
                f"📢 Notified {notified_count} available subcontractor(s).\n"
                "First one to accept will get the job!",
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                f"Job #{job.id} created but sending failed.\n"
                f"Reason: {msg}\n"
                "Please try sending again from 'My Jobs'."
            )
    
    await state.clear()
    await callback.answer("Job created!")

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
            f"*Job Saved!*\n\n"
            f"Job #{job.id}: {job.title}\n"
            f"Status: Created\n\n"
            "You can send it later when subcontractors are available.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text("Failed to create job.")
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("cancel:save_pending"))
async def cancel_save_pending(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Job creation cancelled.")
    await callback.answer()

@router.message(Command("myjobs"))
@require_role(UserRole.SUPERVISOR)
async def cmd_my_jobs(message: Message):
    await show_my_jobs(message)

@router.message(F.text == "📋 My Jobs")
async def btn_my_jobs(message: Message):
    if not await check_supervisor(message):
        return
    await show_my_jobs(message)

@router.message(F.text == "⏳ Pending Jobs")
async def btn_pending_jobs(message: Message):
    if not await check_supervisor(message):
        return
    await show_filtered_jobs(message, [JobStatus.CREATED, JobStatus.SENT], "Pending Jobs")

@router.message(F.text == "🔄 Active Jobs")
async def btn_active_jobs(message: Message):
    if not await check_supervisor(message):
        return
    await show_filtered_jobs(message, [JobStatus.ACCEPTED, JobStatus.IN_PROGRESS], "Active Jobs")

@router.message(F.text == "📥 Submitted Jobs")
async def btn_submitted_jobs(message: Message):
    if not await check_supervisor(message):
        return
    await show_filtered_jobs(message, [JobStatus.SUBMITTED], "Submitted Jobs")

async def check_supervisor(message: Message) -> bool:
    if not async_session:
        await message.answer("Database not available.")
        return False
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != UserRole.SUPERVISOR:
            await message.answer("You don't have permission to view jobs.")
            return False
    return True

async def show_my_jobs(message: Message):
    jobs = await JobService.get_supervisor_jobs(message.from_user.id)
    
    if not jobs:
        await message.answer(
            "*My Jobs*\n\n"
            "You haven't created any jobs yet.\n\n"
            "Tap '+New Job' to create one!",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        "*My Jobs*\n\n"
        "Select a job to view details:",
        reply_markup=get_job_list_keyboard(jobs, context="sup"),
        parse_mode="Markdown"
    )

async def show_filtered_jobs(message: Message, status_filter: list[JobStatus], title: str):
    jobs = await JobService.get_supervisor_jobs(message.from_user.id, status_filter)
    
    if not jobs:
        await message.answer(
            f"*{title}*\n\n"
            f"No jobs found with this status.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        f"*{title}*\n\n"
        f"Found {len(jobs)} job(s):",
        reply_markup=get_job_list_keyboard(jobs, context="sup"),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("view_job:sup:"))
async def view_job_details_supervisor(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[2])
    
    job = await JobService.get_job_by_id(job_id)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    status_emoji = {
        JobStatus.CREATED: "Created",
        JobStatus.SENT: "Sent",
        JobStatus.ACCEPTED: "Accepted",
        JobStatus.IN_PROGRESS: "In Progress",
        JobStatus.SUBMITTED: "Submitted for Review",
        JobStatus.COMPLETED: "Completed",
        JobStatus.CANCELLED: "Cancelled",
        JobStatus.ARCHIVED: "Archived"
    }.get(job.status, "Unknown")
    
    type_text = "Quote" if job.job_type == JobType.QUOTE else "Preset Price"
    
    details = (
        f"*Job #{job.id}*\n\n"
        f"*Title:* {job.title}\n"
        f"*Type:* {type_text}\n"
        f"*Status:* {status_emoji}\n"
    )
    
    if job.description:
        details += f"*Description:* {job.description}\n"
    if job.address:
        details += f"*Address:* {job.address}\n"
    if job.preset_price:
        details += f"*Price:* {job.preset_price}\n"
    
    if job.photos:
        details += "\n📸 *Photo Evidence available*"
    
    if job.rating:
        details += f"\n⭐ *Rating:* {job.rating}/5"
        if job.rating_comment:
            details += f"\n💬 *Comment:* {job.rating_comment}"
    
    details += f"\n*Created:* {job.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    keyboard = get_supervisor_job_actions_keyboard(job.id, job.status.value, job.job_type.value)
    
    await callback.message.edit_text(
        details,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_quotes:"))
async def view_quotes(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    quotes = await QuoteService.get_quotes_for_job(job_id)
    
    if not quotes:
        await callback.answer("No quotes submitted yet", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"*Quotes for Job #{job_id}*\n\n"
        f"{len(quotes)} quote(s) received.\n"
        "Select a quote to view details:",
        reply_markup=get_quotes_keyboard(quotes, job_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("quote_detail:"))
async def view_quote_detail(callback: CallbackQuery):
    quote_id = int(callback.data.split(":")[1])
    
    if not async_session:
        await callback.answer("Database error", show_alert=True)
        return
    
    from src.bot.database import Quote
    async with async_session() as session:
        result = await session.execute(
            select(Quote, User).join(User, Quote.subcontractor_id == User.id).where(Quote.id == quote_id)
        )
        row = result.one_or_none()
    
    if not row:
        await callback.answer("Quote not found", show_alert=True)
        return
    
    quote, user = row
    name = user.first_name or user.username or f"User {user.telegram_id}"
    
    await callback.message.edit_text(
        f"*Quote Details*\n\n"
        f"*Subcontractor:* {name}\n"
        f"*Amount:* {quote.amount}\n"
        f"*Submitted:* {quote.submitted_at.strftime('%Y-%m-%d %H:%M')}\n"
        + (f"*Notes:* {quote.notes}\n" if quote.notes else ""),
        reply_markup=get_quote_detail_keyboard(quote.id, quote.job_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("accept_quote:"))
async def accept_quote(callback: CallbackQuery):
    quote_id = int(callback.data.split(":")[1])
    
    success, msg, sub_id = await QuoteService.accept_quote(quote_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"*Quote Accepted!*\n\n"
            f"{msg}\n\n"
            "The winning subcontractor has been notified.",
            parse_mode="Markdown"
        )
        await callback.answer("Quote accepted!")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("view_submission:"))
async def view_submission(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    job = await JobService.get_job_by_id(job_id)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    if job.photos:
        from src.bot.main import bot
        photo_ids = job.photos.split(",")
        
        try:
            await bot.send_photo(
                callback.from_user.id,
                photo_ids[0],
                caption=f"*Photo proof for Job #{job_id}*\n\n"
                        f"*Title:* {job.title}\n"
                        f"Photos: {len(photo_ids)}\n\n"
                        f"Review this submission and mark as completed if satisfied.",
                parse_mode="Markdown"
            )
            
            for photo_id in photo_ids[1:]:
                await bot.send_photo(callback.from_user.id, photo_id)
            
            await callback.answer(f"Sent {len(photo_ids)} photo(s)!")
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await callback.answer("Failed to send photo", show_alert=True)
    else:
        await callback.answer("No photo submitted for this job", show_alert=True)

@router.callback_query(F.data.startswith("sup_cancel:"))
async def supervisor_cancel_job(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    success, msg = await JobService.cancel_job(job_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"*Job Cancelled*\n\n"
            f"Job #{job_id} has been cancelled.",
            parse_mode="Markdown"
        )
        await callback.answer("Job cancelled")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("sup_complete:"))
async def supervisor_complete_job(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    
    success, msg = await JobService.complete_job(job_id, callback.from_user.id, is_supervisor=True)
    
    if success:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        kb = InlineKeyboardBuilder()
        for i in range(1, 6):
            kb.button(text=f"{i} ⭐", callback_data=f"rate:{job_id}:{i}")
        kb.adjust(5)
        
        await callback.message.edit_text(
            f"*Job Completed*\n\n"
            f"Job #{job_id} has been marked as complete.\n\n"
            "Please rate the subcontractor's work:",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer("Job completed!")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("rate:"))
async def process_rating_selection(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    job_id = int(parts[1])
    rating = int(parts[2])
    
    await state.update_data(rating_job_id=job_id, rating_value=rating)
    await callback.message.edit_text(
        f"*Rating: {rating} ⭐*\n\n"
        "Please provide a short comment about the work (or send /skip):",
        parse_mode="Markdown"
    )
    await state.set_state(RatingStates.waiting_for_comment)
    await callback.answer()

@router.message(StateFilter(RatingStates.waiting_for_comment))
async def process_rating_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    job_id = data.get('rating_job_id')
    rating = data.get('rating_value')
    comment = None if message.text == "/skip" else message.text
    
    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.rating = rating
            job.rating_comment = comment
            await session.commit()
            
    await message.answer(f"Thank you! Rating of {rating} ⭐ saved for Job #{job_id}.")
    await state.clear()

@router.callback_query(F.data == "back:sup")
async def back_to_my_jobs(callback: CallbackQuery):
    jobs = await JobService.get_supervisor_jobs(callback.from_user.id)
    
    await callback.message.edit_text(
        "*My Jobs*\n\n"
        "Select a job to view details:",
        reply_markup=get_job_list_keyboard(jobs, context="sup"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("page:sup:"))
async def handle_supervisor_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[2])
    
    jobs = await JobService.get_supervisor_jobs(callback.from_user.id)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_job_list_keyboard(jobs, page=page, context="sup")
    )
    await callback.answer()
