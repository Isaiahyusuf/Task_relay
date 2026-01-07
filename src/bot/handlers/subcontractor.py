from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from src.bot.database.models import UserRole, JobType
from src.bot.services.jobs import JobService
from src.bot.utils.permissions import require_role
import logging

logger = logging.getLogger(__name__)
router = Router()

class QuoteStates(StatesGroup):
    waiting_for_quote = State()

@router.message(Command("jobs"))
@require_role(UserRole.SUBCONTRACTOR)
async def cmd_jobs(message: Message):
    jobs = await JobService.get_pending_jobs_for_subcontractor(message.from_user.id)
    
    if not jobs:
        await message.answer("You have no pending jobs assigned to you.")
        return
    
    job_list = []
    for job in jobs:
        job_info = (
            f"Job #{job.id}: {job.title}\n"
            f"Type: {job.job_type.value.replace('_', ' ').title()}\n"
        )
        if job.description:
            job_info += f"Description: {job.description}\n"
        if job.address:
            job_info += f"Address: {job.address}\n"
        if job.preset_price:
            job_info += f"Price: {job.preset_price}\n"
        
        job_info += f"\nUse /accept {job.id} or /decline {job.id}"
        job_list.append(job_info)
    
    await message.answer("Your pending jobs:\n\n" + "\n\n---\n\n".join(job_list))

@router.message(Command("accept"))
@require_role(UserRole.SUBCONTRACTOR)
async def cmd_accept(message: Message, state: FSMContext):
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer("Usage: /accept <job_id> [quote_price]")
        return
    
    try:
        job_id = int(parts[1])
    except ValueError:
        await message.answer("Invalid job ID. Usage: /accept <job_id>")
        return
    
    jobs = await JobService.get_pending_jobs_for_subcontractor(message.from_user.id)
    job = next((j for j in jobs if j.id == job_id), None)
    
    if not job:
        await message.answer("Job not found or not assigned to you.")
        return
    
    quoted_price = None
    if job.job_type == JobType.QUOTE:
        if len(parts) < 3:
            await state.update_data(accepting_job_id=job_id)
            await message.answer(
                f"This is a quote job. Please enter your quote price:\n"
                f"(or type /cancel to cancel)"
            )
            await state.set_state(QuoteStates.waiting_for_quote)
            return
        quoted_price = parts[2]
    
    success, msg = await JobService.accept_job(job_id, message.from_user.id, quoted_price)
    await message.answer(msg)

@router.message(StateFilter(QuoteStates.waiting_for_quote))
async def process_quote(message: Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Quote cancelled.")
        return
    
    data = await state.get_data()
    job_id = data.get('accepting_job_id')
    
    if not job_id:
        await state.clear()
        await message.answer("Session expired. Please use /accept again.")
        return
    
    success, msg = await JobService.accept_job(job_id, message.from_user.id, message.text.strip())
    await message.answer(msg)
    await state.clear()

@router.message(Command("decline"))
@require_role(UserRole.SUBCONTRACTOR)
async def cmd_decline(message: Message):
    parts = message.text.split(maxsplit=2)
    
    if len(parts) < 2:
        await message.answer("Usage: /decline <job_id> [reason]")
        return
    
    try:
        job_id = int(parts[1])
    except ValueError:
        await message.answer("Invalid job ID. Usage: /decline <job_id>")
        return
    
    reason = parts[2] if len(parts) > 2 else None
    
    success, msg = await JobService.decline_job(job_id, message.from_user.id, reason)
    await message.answer(msg)
