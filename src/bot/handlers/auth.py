from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from src.bot.database import async_session, User
from src.bot.database.models import UserRole
from src.bot.services.access_codes import AccessCodeService
from src.bot.utils.keyboards import get_main_menu_keyboard, get_self_delete_confirm_keyboard
from src.bot.config import config
import logging

logger = logging.getLogger(__name__)
router = Router()

class AuthStates(StatesGroup):
    waiting_for_code = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    if not async_session:
        await message.answer("Bot is not properly configured. Please contact an administrator.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            # Check if super admin code is still valid
            if user.role == UserRole.SUPER_ADMIN:
                if not config.SUPER_ADMIN_CODE or user.super_admin_code != config.SUPER_ADMIN_CODE:
                    # Super admin code has changed, invalidate this user
                    user.is_active = False
                    user.role = UserRole.SUBCONTRACTOR  # Reset to lowest role
                    await session.commit()
                    await message.answer(
                        "*Access Revoked*\n\n"
                        "Your super admin access has been revoked because the access code was changed.\n\n"
                        "Please enter a new access code to continue:",
                        parse_mode="Markdown"
                    )
                    await state.set_state(AuthStates.waiting_for_code)
                    return
            
            role_name = user.role.value.replace("_", " ").title()
            keyboard = get_main_menu_keyboard(user.role)
            await message.answer(
                f"Welcome back, {message.from_user.first_name or 'there'}!\n\n"
                f"You are logged in as: *{role_name}*\n\n"
                "Use the menu below to navigate:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await state.clear()
            return
    
    await message.answer(
        "*Welcome to TaskRelay Bot!*\n\n"
        "This is a workflow automation and job dispatch system.\n\n"
        "Please enter your access code to begin:",
        parse_mode="Markdown"
    )
    await state.set_state(AuthStates.waiting_for_code)

@router.message(StateFilter(AuthStates.waiting_for_code))
async def process_access_code(message: Message, state: FSMContext):
    code = message.text.strip()
    
    success, response = await AccessCodeService.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        code=code
    )
    
    if success:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()
        
        if user:
            keyboard = get_main_menu_keyboard(user.role)
            await message.answer(
                f"{response}\n\n"
                "Use the menu below to get started:",
                reply_markup=keyboard
            )
        else:
            await message.answer(response)
        await state.clear()
    else:
        await message.answer(
            f"{response}\n\n"
            "Please try again with a valid access code:"
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await show_help(message)

@router.message(F.text == "ℹ️ Help")
async def btn_help(message: Message):
    await show_help(message)

@router.message(F.text == "🗑️ Delete My Account")
async def btn_delete_account(message: Message):
    if not async_session:
        await message.answer("Database not available.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("You are not registered.")
            return
    
    await message.answer(
        "⚠️ *Delete Your Account*\n\n"
        "Are you sure you want to delete your account?\n\n"
        "*This action cannot be undone.*\n"
        "You will need a new access code to register again.",
        reply_markup=get_self_delete_confirm_keyboard(user.id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("confirm_self_delete:"))
async def handle_confirm_self_delete(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id, User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("User not found", show_alert=True)
            return
        
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
    
    await callback.message.edit_text(
        "Your account has been deleted.\n\n"
        "Use /start with a new access code to register again."
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_self_delete")
async def handle_cancel_self_delete(callback: CallbackQuery):
    await callback.message.edit_text("Account deletion cancelled.")
    await callback.answer()

@router.message(F.text == "📘 About")
async def btn_about(message: Message):
    about_text = (
        "🤖 *About TaskRelay Bot*\n\n"
        "TaskRelay is a comprehensive workflow automation system designed to streamline the connection "
        "between supervisors who need work done and subcontractors who perform it.\n\n"
        "📊 *Job Lifecycle Explained:*\n"
        "• *CREATED:* Job is drafted by a supervisor.\n"
        "• *SENT:* Dispatched to a subcontractor (Preset Price) or open for bids (Quote Job).\n"
        "• *ACCEPTED:* Subcontractor has committed to the work.\n"
        "• *IN_PROGRESS:* Work is currently being performed.\n"
        "• *COMPLETED:* Work is finished and pending supervisor review.\n\n"
        "🔧 *Subcontractor Tools:*\n"
        "• Submit binding quotes for bidding jobs.\n"
        "• Manage availability (Available/Busy/Away) to control incoming work.\n"
        "• Real-time buttons to accept, start, and finish tasks.\n\n"
        "👔 *Supervisor Tools:*\n"
        "• Create detailed job postings with photos and locations.\n"
        "• Compare multiple subcontractor quotes side-by-side.\n"
        "• Monitor team progress in real-time via filtered dashboards.\n\n"
        "⚡ *Automation Details:*\n"
        "• *Smart Reminders:* Sent if a job is ignored for 24 hours.\n"
        "• *Auto-Cancel:* Unanswered jobs close after 72 hours to free up the request.\n"
        "• *Archives:* 90-day auto-archiving keeps your history clean and searchable.\n\n"
        "_Version 1.0.0 - Built for efficiency and reliability._"
    )
    await message.answer(about_text, parse_mode="Markdown")

async def show_help(message: Message):
    if not async_session:
        await message.answer("Bot is not properly configured.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                "You are not registered.\n\n"
                "Please use /start to register with your access code."
            )
            return
        
        if user.role == UserRole.SUPER_ADMIN:
            help_text = (
                "*SUPER ADMIN MANUAL*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                
                "*USER MANAGEMENT*\n"
                "• *Create Admin Code* - Generate codes for new admins\n"
                "• *Create Supervisor Code* - Generate codes for supervisors\n"
                "• *Create Subcontractor Code* - Generate codes for workers\n"
                "• *All Access Codes* - View all generated codes\n"
                "• *View Admins/Supervisors/Subcontractors* - Manage users by role\n"
                "• *All Users* - View complete user list\n"
                "• *View By Teams* - See users grouped by team\n\n"
                
                "*JOB MANAGEMENT*\n"
                "• *New Job* - Create and dispatch jobs\n"
                "• *Job History* - View all job records\n"
                "• *Archive Jobs* - Archive old completed jobs\n"
                "• *View Archived* - Browse archived jobs\n\n"
                
                "*COMMUNICATION*\n"
                "• *Send Message* - Message subcontractors (all/team/select)\n"
                "• *Weekly Availability* - View subcontractor schedules\n\n"
                
                "*OTHER*\n"
                "• *Switch Role* - Test other role views\n"
                "• *About* - Bot information"
            )
        elif user.role == UserRole.ADMIN:
            help_text = (
                "*ADMIN MANUAL*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                
                "*USER MANAGEMENT*\n"
                "• *Create Access Code* - Generate codes for supervisors and subcontractors\n"
                "• *Manage Users* - View and manage all users\n"
                "• *View By Teams* - See users grouped by team\n\n"
                
                "*JOB MANAGEMENT*\n"
                "• *New Job* - Create and dispatch jobs to subcontractors\n"
                "• *Job History* - View all job records\n"
                "• *Archive Jobs* - Archive old completed jobs\n"
                "• *View Archived* - Browse archived jobs\n\n"
                
                "*COMMUNICATION*\n"
                "• *Send Message* - Message subcontractors (all/team/select)\n"
                "• *Weekly Availability* - View subcontractor schedules\n\n"
                
                "*HOW TO CREATE A JOB*\n"
                "1. Tap *New Job*\n"
                "2. Choose job type (Quote or Preset Price)\n"
                "3. Enter job title and description\n"
                "4. Add optional photos and deadline\n"
                "5. Select target team or send bot-wide\n\n"
                
                "*OTHER*\n"
                "• *Switch Role* - Test other role views\n"
                "• *About* - Bot information"
            )
        elif user.role == UserRole.SUPERVISOR:
            help_text = (
                "*SUPERVISOR MANUAL*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                
                "*JOB CREATION*\n"
                "• *New Job* - Create and dispatch jobs\n"
                "  1. Choose: Quote Job or Preset Price\n"
                "  2. Enter title, description, price (if preset)\n"
                "  3. Add photos (optional) - repair images\n"
                "  4. Set deadline (optional) - DD/MM/YYYY\n"
                "  5. Select team or send bot-wide\n\n"
                
                "*JOB TRACKING*\n"
                "• *My Jobs* - View all your jobs\n"
                "• *Pending Jobs* - Jobs awaiting response\n"
                "• *Active Jobs* - Jobs in progress\n"
                "• *Submitted Jobs* - Jobs ready for review\n\n"
                
                "*JOB ACTIONS*\n"
                "• *View Quotes* - Compare quotes from subcontractors\n"
                "• *Accept Quote* - Select winning quote\n"
                "• *Cancel Job* - Cancel unstarted jobs\n"
                "• *Mark Complete* - Close job with star rating\n"
                "• *Not Satisfied* - Request revision with feedback\n\n"
                
                "*COMMUNICATION*\n"
                "• *Send Message* - Message subcontractors\n"
                "• *View Availability* - Check subcontractor schedules\n"
                "• *Create Subcontractor Code* - Add new workers\n\n"
                
                "*STAR RATINGS*\n"
                "When marking complete, rate 1-5 stars.\n"
                "Ratings help track subcontractor performance."
            )
        else:  # SUBCONTRACTOR
            help_text = (
                "*SUBCONTRACTOR MANUAL*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                
                "*FINDING JOBS*\n"
                "• *Available Jobs* - View jobs waiting for you\n"
                "• *My Active Jobs* - Jobs you're working on\n\n"
                
                "*RESPONDING TO JOBS*\n"
                "• *Accept* - Take the job (enter company name)\n"
                "• *Decline* - Reject with reason\n"
                "• *Submit Quote* - For quote-type jobs, enter your price\n\n"
                
                "*COMPLETING JOBS*\n"
                "• *Start Job* - Begin work on accepted job\n"
                "• *Submit Job* - Finish with notes and photo proof\n"
                "• Supervisor reviews and marks complete\n\n"
                
                "*AVAILABILITY STATUS*\n"
                "Set your current status:\n"
                "• *Available* (green) - Ready for new jobs\n"
                "• *Busy* (yellow) - Temporarily unavailable\n"
                "• *Away* (red) - Not accepting jobs\n\n"
                
                "*WEEKLY AVAILABILITY*\n"
                "• *My Availability* - View/update weekly schedule\n"
                "• Every Thursday: Tick days you can work (Mon-Fri)\n"
                "• Add notes for specific days if needed\n\n"
                
                "*COMMUNICATION*\n"
                "• *Report Unavailability* - Notify supervisors\n"
                "• When you receive messages, tap:\n"
                "  - *Acknowledge* - Confirm you've seen it\n"
                "  - *Reply* - Send a response\n\n"
                
                "*TIPS*\n"
                "• Submit jobs with clear photos\n"
                "• Keep your availability updated\n"
                "• Respond to jobs promptly"
            )
        
        await message.answer(help_text, parse_mode="Markdown")
