from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from src.bot.database import async_session, User, Job
from src.bot.database.models import UserRole, JobType, JobStatus
from src.bot.services.jobs import JobService
from src.bot.utils.permissions import require_role
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

@router.message(Command("newjob"))
@require_role(UserRole.SUPERVISOR)
async def cmd_new_job(message: Message, state: FSMContext):
    await message.answer("Creating a new job.\n\nPlease enter the job title:")
    await state.set_state(NewJobStates.waiting_for_title)

@router.message(StateFilter(NewJobStates.waiting_for_title))
async def process_job_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Quote Job", callback_data="job_type_quote")],
        [InlineKeyboardButton(text="Preset Price Job", callback_data="job_type_preset")]
    ])
    
    await message.answer("Select job type:", reply_markup=keyboard)
    await state.set_state(NewJobStates.waiting_for_type)

@router.callback_query(F.data.startswith("job_type_"), StateFilter(NewJobStates.waiting_for_type))
async def process_job_type(callback: CallbackQuery, state: FSMContext):
    job_type = JobType.QUOTE if callback.data == "job_type_quote" else JobType.PRESET_PRICE
    await state.update_data(job_type=job_type)
    
    await callback.message.edit_text(
        f"Job type: {job_type.value.replace('_', ' ').title()}\n\n"
        "Enter job description (or send 'skip' to skip):"
    )
    await state.set_state(NewJobStates.waiting_for_description)
    await callback.answer()

@router.message(StateFilter(NewJobStates.waiting_for_description))
async def process_job_description(message: Message, state: FSMContext):
    description = None if message.text.lower().strip() == "skip" else message.text.strip()
    await state.update_data(description=description)
    
    await message.answer("Enter the job address (or send 'skip' to skip):")
    await state.set_state(NewJobStates.waiting_for_address)

@router.message(StateFilter(NewJobStates.waiting_for_address))
async def process_job_address(message: Message, state: FSMContext):
    address = None if message.text.lower().strip() == "skip" else message.text.strip()
    await state.update_data(address=address)
    
    data = await state.get_data()
    
    if data['job_type'] == JobType.PRESET_PRICE:
        await message.answer("Enter the preset price:")
        await state.set_state(NewJobStates.waiting_for_price)
    else:
        await show_subcontractor_selection(message, state)

@router.message(StateFilter(NewJobStates.waiting_for_price))
async def process_job_price(message: Message, state: FSMContext):
    await state.update_data(preset_price=message.text.strip())
    await show_subcontractor_selection(message, state)

async def show_subcontractor_selection(message: Message, state: FSMContext):
    if not async_session:
        await message.answer("Database error. Please try again.")
        await state.clear()
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        supervisor = result.scalar_one_or_none()
        
        subcontractors_result = await session.execute(
            select(User).where(
                User.role == UserRole.SUBCONTRACTOR,
                User.team_id == supervisor.team_id,
                User.is_active == True
            )
        )
        subcontractors = subcontractors_result.scalars().all()
    
    if not subcontractors:
        await message.answer("No subcontractors available in your team. Job saved as pending.")
        await create_job_without_dispatch(message, state)
        return
    
    buttons = [
        [InlineKeyboardButton(
            text=f"{s.first_name or s.username or f'User {s.telegram_id}'}",
            callback_data=f"assign_{s.id}"
        )]
        for s in subcontractors
    ]
    buttons.append([InlineKeyboardButton(text="Save without dispatching", callback_data="assign_none")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer("Select a subcontractor to dispatch the job to:", reply_markup=keyboard)
    await state.set_state(NewJobStates.waiting_for_subcontractor)

async def create_job_without_dispatch(message: Message, state: FSMContext):
    data = await state.get_data()
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        supervisor = result.scalar_one_or_none()
    
    job = await JobService.create_job(
        supervisor_id=supervisor.id,
        title=data['title'],
        job_type=data['job_type'],
        description=data.get('description'),
        address=data.get('address'),
        preset_price=data.get('preset_price'),
        team_id=supervisor.team_id
    )
    
    if job:
        await message.answer(f"Job #{job.id} created successfully!")
    else:
        await message.answer("Failed to create job. Please try again.")
    
    await state.clear()

@router.callback_query(F.data.startswith("assign_"), StateFilter(NewJobStates.waiting_for_subcontractor))
async def process_subcontractor_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        supervisor = result.scalar_one_or_none()
    
    job = await JobService.create_job(
        supervisor_id=supervisor.id,
        title=data['title'],
        job_type=data['job_type'],
        description=data.get('description'),
        address=data.get('address'),
        preset_price=data.get('preset_price'),
        team_id=supervisor.team_id
    )
    
    if not job:
        await callback.message.edit_text("Failed to create job. Please try again.")
        await state.clear()
        await callback.answer()
        return
    
    if callback.data == "assign_none":
        await callback.message.edit_text(f"Job #{job.id} created and saved as pending.")
    else:
        subcontractor_id = int(callback.data.replace("assign_", ""))
        success = await JobService.dispatch_job(job.id, subcontractor_id)
        
        if success:
            await callback.message.edit_text(f"Job #{job.id} created and dispatched!")
        else:
            await callback.message.edit_text(f"Job #{job.id} created but dispatch failed.")
    
    await state.clear()
    await callback.answer()

@router.message(Command("myjobs"))
@require_role(UserRole.SUPERVISOR)
async def cmd_my_jobs(message: Message):
    if not async_session:
        await message.answer("Database error.")
        return
    
    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        jobs_result = await session.execute(
            select(Job).where(Job.supervisor_id == user.id).order_by(Job.created_at.desc()).limit(10)
        )
        jobs = jobs_result.scalars().all()
    
    if not jobs:
        await message.answer("You haven't created any jobs yet.")
        return
    
    job_list = "\n\n".join([
        f"#{j.id}: {j.title}\nStatus: {j.status.value}\nType: {j.job_type.value}"
        for j in jobs
    ])
    
    await message.answer(f"Your recent jobs:\n\n{job_list}")
