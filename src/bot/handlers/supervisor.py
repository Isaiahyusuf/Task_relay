from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from src.bot.database import async_session, User, Job, Quote
from src.bot.database.models import UserRole, JobType, JobStatus, AvailabilityStatus
from src.bot.services.jobs import JobService
from src.bot.services.quotes import QuoteService
from src.bot.services.access_codes import AccessCodeService
from src.bot.handlers.admin import CreateCodeStates
from src.bot.utils.permissions import require_role
from src.bot.utils.keyboards import (
    get_job_type_keyboard, get_skip_keyboard,
    get_confirmation_keyboard, get_job_list_keyboard, get_main_menu_keyboard, 
    get_back_keyboard, get_supervisor_job_actions_keyboard, get_quotes_keyboard,
    get_quote_detail_keyboard, get_skip_photos_keyboard, get_skip_deadline_keyboard
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
    waiting_for_photos = State()
    waiting_for_deadline = State()
    waiting_for_subcontractor = State()
    confirming = State()

class RatingStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_comment = State()

class DeclineQuoteStates(StatesGroup):
    waiting_for_reason = State()

class NotSatisfiedStates(StatesGroup):
    waiting_for_reason = State()

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
        await ask_for_photos(callback.message, state, edit=True)
    await callback.answer()

@router.message(StateFilter(NewJobStates.waiting_for_address))
async def process_job_address(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please enter a text address or location:")
        return
    
    if message.text.startswith("/"):
        await message.answer("Job creation cancelled.")
        await state.clear()
        return
        
    await state.update_data(address=message.text.strip())
    data = await state.get_data()
    
    job_type = data.get('job_type')
    if not job_type:
        await message.answer("Session expired. Please start over with /start")
        await state.clear()
        return
    
    if job_type == JobType.PRESET_PRICE:
        await ask_for_price(message, state, edit=False)
    else:
        await ask_for_photos(message, state, edit=False)

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
    await ask_for_photos(message, state, edit=False)

async def ask_for_photos(message: Message, state: FSMContext, edit: bool = False):
    text = (
        "*Creating a New Job*\n\n"
        "Step 5/7: Attach repair photos (optional)\n\n"
        "Send photos of the repair work, or skip."
    )
    keyboard = get_skip_photos_keyboard()
    await state.update_data(supervisor_photos=[])
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.set_state(NewJobStates.waiting_for_photos)

@router.callback_query(F.data == "skip:photos", StateFilter(NewJobStates.waiting_for_photos))
async def skip_photos(callback: CallbackQuery, state: FSMContext):
    await state.update_data(supervisor_photos=[])
    await ask_for_deadline(callback.message, state, edit=True)
    await callback.answer()

@router.message(StateFilter(NewJobStates.waiting_for_photos))
async def process_supervisor_photo(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/done"):
        await ask_for_deadline(message, state, edit=False)
        return
    
    if message.text and message.text.startswith("/"):
        await message.answer("Job creation cancelled.")
        await state.clear()
        return
    
    if not message.photo:
        await message.answer(
            "Please send a photo, or use the Skip button.\n"
            "Type /done when finished adding photos."
        )
        return
    
    photo = message.photo[-1]
    data = await state.get_data()
    photos = data.get('supervisor_photos', [])
    photos.append(photo.file_id)
    await state.update_data(supervisor_photos=photos)
    
    await message.answer(
        f"Photo {len(photos)} added.\n\n"
        f"Send more photos or type /done to continue."
    )

async def ask_for_deadline(message: Message, state: FSMContext, edit: bool = False):
    text = (
        "*Creating a New Job*\n\n"
        "Step 6/7: Set a deadline (optional)\n\n"
        "Enter deadline date in format: DD/MM/YYYY\n"
        "Example: 15/02/2026"
    )
    keyboard = get_skip_deadline_keyboard()
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.set_state(NewJobStates.waiting_for_deadline)

@router.callback_query(F.data == "skip:deadline", StateFilter(NewJobStates.waiting_for_deadline))
async def skip_deadline(callback: CallbackQuery, state: FSMContext):
    await state.update_data(deadline=None)
    await show_team_selection(callback.message, state, callback.from_user.id, edit=True)
    await callback.answer()

@router.message(StateFilter(NewJobStates.waiting_for_deadline))
async def process_job_deadline(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/"):
        await message.answer("Job creation cancelled.")
        await state.clear()
        return
    
    from datetime import datetime
    try:
        deadline = datetime.strptime(message.text.strip(), "%d/%m/%Y")
        if deadline < datetime.now():
            await message.answer("Deadline cannot be in the past. Please enter a future date (DD/MM/YYYY):")
            return
        await state.update_data(deadline=deadline)
        await show_team_selection(message, state, message.from_user.id, edit=False)
    except ValueError:
        await message.answer("Invalid date format. Please use DD/MM/YYYY (e.g., 15/02/2026):")

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
    
    if not supervisor:
        await message.answer("User not found. Please register first with /start")
        await state.clear()
        return
    
    await state.update_data(supervisor_id=supervisor.id, team_id=supervisor.team_id)
    
    from src.bot.utils.keyboards import get_job_team_selection_keyboard
    text = (
        "*Creating a New Job*\n\n"
        "Final step: Where do you want to send this job?\n\n"
        "*Bot-Wide* - All available subcontractors\n"
        "*North/West* - North/West subcontractors only\n"
        "*South/East* - South/East subcontractors only"
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
    
    # Prepare supervisor photos
    sup_photos = data.get('supervisor_photos', [])
    photos_str = ",".join(sup_photos) if sup_photos else None
    
    job = await JobService.create_job(
        supervisor_id=data['supervisor_id'],
        title=data['title'],
        job_type=data['job_type'],
        description=data.get('description'),
        address=data.get('address'),
        preset_price=data.get('preset_price'),
        team_id=data.get('team_id'),
        supervisor_photos=photos_str,
        deadline=data.get('deadline')
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
            logger.info(f"Starting notification process. send_option={send_option}")
            async with async_session() as session:
                from sqlalchemy import or_
                
                # First, log ALL users in the database for debugging
                all_users_result = await session.execute(select(User))
                all_users = list(all_users_result.scalars().all())
                logger.info(f"Total users in database: {len(all_users)}")
                for u in all_users:
                    logger.info(f"  User {u.id}: role={u.role}, telegram_id={u.telegram_id}, team_id={u.team_id}")
                
                if send_option == "all":
                    # Get ALL subcontractors regardless of availability
                    logger.info("Querying for ALL subcontractors (bot-wide)")
                    result = await session.execute(
                        select(User).where(User.role == UserRole.SUBCONTRACTOR)
                    )
                    team_label = "all subcontractors (bot-wide)"
                else:
                    # Get team by type
                    team_type = TeamType.NORTHWEST if send_option == "northwest" else TeamType.SOUTHEAST
                    team_result = await session.execute(
                        select(Team).where(Team.team_type == team_type)
                    )
                    team = team_result.scalar_one_or_none()
                    
                    if team:
                        # Get ALL subcontractors in this team regardless of availability
                        result = await session.execute(
                            select(User).where(
                                User.role == UserRole.SUBCONTRACTOR,
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
                logger.info(f"=== JOB NOTIFICATION START ===")
                logger.info(f"Job ID: {job.id}, Title: {job.title}")
                logger.info(f"Send option: {send_option}")
                logger.info(f"Found {len(available_subs)} subcontractors to notify")
                
                if len(available_subs) == 0:
                    logger.warning("NO SUBCONTRACTORS FOUND! Check if any users have role=SUBCONTRACTOR in the database.")
                
                # Use callback.bot - the correct aiogram 3.x way to get the bot instance
                bot = callback.bot
                logger.info(f"Bot instance from callback: {bot}")
                
                notified_count = 0
                failed_count = 0
                
                # Prepare deadline text
                deadline_text = ""
                if job.deadline:
                    deadline_text = f"\nDeadline: {job.deadline.strftime('%d/%m/%Y')}"
                
                # Get supervisor photos
                sup_photos = job.supervisor_photos.split(",") if job.supervisor_photos else []
                
                for sub in available_subs:
                    try:
                        logger.info(f"[NOTIFY] Sending to subcontractor id={sub.id}, telegram_id={sub.telegram_id}, name={sub.first_name}")
                        await bot.send_message(
                            sub.telegram_id,
                            f"🆕 *New Job Available*\n\n"
                            f"Job #{job.id}: {job.title}\n"
                            f"Location: {job.address or 'N/A'}\n"
                            f"Price: {job.preset_price or 'N/A'}{deadline_text}\n\n"
                            f"Check 'Available Jobs' to accept this job!",
                            parse_mode="Markdown"
                        )
                        
                        # Send supervisor photos if any
                        if sup_photos:
                            from aiogram.types import InputMediaPhoto
                            if len(sup_photos) == 1:
                                await bot.send_photo(sub.telegram_id, sup_photos[0], caption="📷 Repair photos for this job")
                            else:
                                media_group = [InputMediaPhoto(media=photo_id) for photo_id in sup_photos]
                                media_group[0] = InputMediaPhoto(media=sup_photos[0], caption="📷 Repair photos for this job")
                                await bot.send_media_group(sub.telegram_id, media_group)
                        
                        notified_count += 1
                        logger.info(f"[NOTIFY SUCCESS] Notified subcontractor telegram_id={sub.telegram_id}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"[NOTIFY FAILED] subcontractor telegram_id={sub.telegram_id}: {e}", exc_info=True)
                
                logger.info(f"=== JOB NOTIFICATION COMPLETE ===")
                logger.info(f"Total: {len(available_subs)}, Success: {notified_count}, Failed: {failed_count}")
                
            
            await callback.message.edit_text(
                f"*Job Created & Sent!*\n\n"
                f"Job #{job.id}: {job.title}\n"
                f"Sent to: {team_label}\n\n"
                f"📢 Notified {notified_count} subcontractor(s).\n"
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
    
    # Prepare supervisor photos
    sup_photos = data.get('supervisor_photos', [])
    photos_str = ",".join(sup_photos) if sup_photos else None
    
    job = await JobService.create_job(
        supervisor_id=data['supervisor_id'],
        title=data['title'],
        job_type=data['job_type'],
        description=data.get('description'),
        address=data.get('address'),
        preset_price=data.get('preset_price'),
        team_id=data.get('team_id'),
        supervisor_photos=photos_str,
        deadline=data.get('deadline')
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
    
    success, msg, sub_telegram_id, job_id, job_title, quote_amount = await QuoteService.accept_quote(quote_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"*Quote Accepted!*\n\n"
            f"Job #{job_id}: {job_title}\n"
            f"Accepted Quote: *{quote_amount}*\n\n"
            "The winning subcontractor has been notified.",
            parse_mode="Markdown"
        )
        await callback.answer("Quote accepted!")
        
        # Notify the winning subcontractor
        if sub_telegram_id:
            bot = callback.bot
            if bot:
                try:
                    await bot.send_message(
                        sub_telegram_id,
                        f"🎉 *Your Quote Was Accepted!*\n\n"
                        f"Job #{job_id}: {job_title}\n"
                        f"Your Quote: *{quote_amount}*\n\n"
                        f"Congratulations! The job is now assigned to you.\n"
                        f"Check 'My Active Jobs' to start working on it.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify subcontractor {sub_telegram_id} of quote acceptance: {e}")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("decline_quote:"))
async def decline_quote_start(callback: CallbackQuery, state: FSMContext):
    quote_id = int(callback.data.split(":")[1])
    
    # Get quote info for display
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
    
    await state.update_data(declining_quote_id=quote_id, quote_amount=quote.amount, subcontractor_name=name)
    
    await callback.message.edit_text(
        f"*Decline Quote*\n\n"
        f"You are declining the quote from *{name}* for *{quote.amount}*.\n\n"
        f"Please provide a reason for declining (this will be sent to the subcontractor):",
        parse_mode="Markdown"
    )
    await state.set_state(DeclineQuoteStates.waiting_for_reason)
    await callback.answer()

@router.message(StateFilter(DeclineQuoteStates.waiting_for_reason))
async def process_decline_reason(message: Message, state: FSMContext):
    reason = message.text.strip()
    
    if len(reason) < 5:
        await message.answer("Please provide a meaningful reason (at least 5 characters):")
        return
    
    data = await state.get_data()
    quote_id = data.get('declining_quote_id')
    quote_amount = data.get('quote_amount')
    subcontractor_name = data.get('subcontractor_name')
    
    success, msg, sub_telegram_id, job_id, job_title = await QuoteService.decline_quote(
        quote_id, message.from_user.id, reason
    )
    
    if success:
        await message.answer(
            f"*Quote Declined*\n\n"
            f"Quote from *{subcontractor_name}* for *{quote_amount}* has been declined.\n\n"
            f"The subcontractor has been notified and can submit a new quote.",
            parse_mode="Markdown"
        )
        
        # Notify the subcontractor
        if sub_telegram_id:
            bot = message.bot
            if bot:
                try:
                    await bot.send_message(
                        sub_telegram_id,
                        f"❌ *Quote Declined*\n\n"
                        f"Your quote for Job #{job_id}: {job_title}\n"
                        f"Amount: *{quote_amount}*\n\n"
                        f"*Reason:* {reason}\n\n"
                        f"You can submit a new quote for this job if you wish.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify subcontractor {sub_telegram_id} of quote decline: {e}")
    else:
        await message.answer(f"Error: {msg}")
    
    await state.clear()

@router.callback_query(F.data.startswith("view_submission:"))
async def view_submission(callback: CallbackQuery):
    job_id = int(callback.data.split(":")[1])
    
    job = await JobService.get_job_by_id(job_id)
    
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    if job.photos:
        bot = callback.bot
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
    
    subcontractor_tg_id = None
    job_title = ""
    
    async with async_session() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.rating = rating
            job.rating_comment = comment
            job_title = job.title
            
            # Get subcontractor's telegram_id
            if job.subcontractor_id:
                sub_result = await session.execute(
                    select(User).where(User.id == job.subcontractor_id)
                )
                sub = sub_result.scalar_one_or_none()
                if sub:
                    subcontractor_tg_id = sub.telegram_id
            
            await session.commit()
    
    # Notify subcontractor of the rating
    if subcontractor_tg_id:
        bot = message.bot
        if bot:
            try:
                stars = "⭐" * rating
                comment_text = f"\nComment: {comment}" if comment else ""
                await bot.send_message(
                    subcontractor_tg_id,
                    f"🎉 *Job Completed & Rated!*\n\n"
                    f"Job #{job_id}: {job_title}\n\n"
                    f"Your rating: {stars} ({rating}/5){comment_text}\n\n"
                    f"Thank you for your work!",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify subcontractor {subcontractor_tg_id} of rating: {e}")
            
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

# ============= NOT SATISFIED FLOW =============

@router.callback_query(F.data.startswith("sup_not_satisfied:"))
async def supervisor_not_satisfied(callback: CallbackQuery, state: FSMContext):
    job_id = int(callback.data.split(":")[1])
    
    job = await JobService.get_job_by_id(job_id)
    if not job:
        await callback.answer("Job not found", show_alert=True)
        return
    
    await state.update_data(not_satisfied_job_id=job_id)
    await state.set_state(NotSatisfiedStates.waiting_for_reason)
    
    await callback.message.edit_text(
        f"*Not Satisfied with Job #{job_id}*\n\n"
        f"Job: {job.title}\n\n"
        "Please explain why you are not satisfied with this work.\n"
        "This feedback will be sent to the subcontractor:",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(StateFilter(NotSatisfiedStates.waiting_for_reason))
async def process_not_satisfied_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    job_id = data.get('not_satisfied_job_id')
    reason = message.text.strip()
    
    if not reason:
        await message.answer("Please provide a reason for your dissatisfaction:")
        return
    
    async with async_session() as session:
        # Get job details
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            await message.answer("Job not found.")
            await state.clear()
            return
        
        # Get subcontractor
        sub_result = await session.execute(
            select(User).where(User.id == job.subcontractor_id)
        )
        subcontractor = sub_result.scalar_one_or_none()
        
        # Update job status back to IN_PROGRESS so subcontractor can resubmit
        job.status = JobStatus.IN_PROGRESS
        job.notes = f"Revision requested: {reason}"
        await session.commit()
        
        # Notify subcontractor
        if subcontractor:
            try:
                bot = message.bot
                await bot.send_message(
                    subcontractor.telegram_id,
                    f"⚠️ *Revision Requested*\n\n"
                    f"Job #{job_id}: {job.title}\n\n"
                    f"*Supervisor Feedback:*\n{reason}\n\n"
                    "Please address the issues and resubmit your work.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify subcontractor: {e}")
    
    await message.answer(
        f"*Feedback Sent*\n\n"
        f"Job #{job_id} has been sent back to the subcontractor for revision.\n\n"
        f"Your feedback:\n_{reason}_",
        parse_mode="Markdown"
    )
    await state.clear()
