from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from src.bot.database.models import UserRole, JobStatus

def get_main_menu_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    if role == UserRole.ADMIN:
        buttons = [
            [KeyboardButton(text="📊 Job History"), KeyboardButton(text="📦 Archive Jobs")],
            [KeyboardButton(text="🔑 Create Access Code"), KeyboardButton(text="📋 View Archived")],
            [KeyboardButton(text="ℹ️ Help")]
        ]
    elif role == UserRole.SUPERVISOR:
        buttons = [
            [KeyboardButton(text="➕ New Job"), KeyboardButton(text="📋 My Jobs")],
            [KeyboardButton(text="ℹ️ Help")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="📋 My Assigned Jobs")],
            [KeyboardButton(text="ℹ️ Help")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_job_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Quote Job", callback_data="job_type:quote")],
        [InlineKeyboardButton(text="🏷️ Preset Price Job", callback_data="job_type:preset")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="job_cancel")]
    ])

def get_skip_keyboard(field: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Skip", callback_data=f"skip:{field}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="job_cancel")]
    ])

def get_confirmation_keyboard(action: str, item_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data=f"confirm:{action}:{item_id}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"cancel:{action}:{item_id}")
        ]
    ])

def get_subcontractor_selection_keyboard(subcontractors: list, include_skip: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    for sub in subcontractors:
        name = sub.first_name or sub.username or f"User {sub.telegram_id}"
        buttons.append([InlineKeyboardButton(text=f"👤 {name}", callback_data=f"assign:{sub.id}")])
    
    if include_skip:
        buttons.append([InlineKeyboardButton(text="💾 Save without dispatching", callback_data="assign:none")])
    
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="job_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_job_actions_keyboard(job_id: int, job_type: str = "preset") -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Accept", callback_data=f"job_accept:{job_id}"),
            InlineKeyboardButton(text="❌ Decline", callback_data=f"job_decline:{job_id}")
        ]
    ]
    if job_type == "quote":
        buttons[0].insert(1, InlineKeyboardButton(text="💬 Submit Quote", callback_data=f"job_quote:{job_id}"))
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_job_list_keyboard(jobs: list, page: int = 0, page_size: int = 5, context: str = "history") -> InlineKeyboardMarkup:
    start = page * page_size
    end = start + page_size
    page_jobs = jobs[start:end]
    
    buttons = []
    for job in page_jobs:
        status_emoji = {
            JobStatus.PENDING: "⏳",
            JobStatus.DISPATCHED: "📤",
            JobStatus.ACCEPTED: "✅",
            JobStatus.DECLINED: "❌",
            JobStatus.COMPLETED: "✔️",
            JobStatus.ARCHIVED: "📦"
        }.get(job.status, "📋")
        
        buttons.append([InlineKeyboardButton(
            text=f"{status_emoji} #{job.id}: {job.title[:30]}",
            callback_data=f"view_job:{context}:{job.id}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"page:{context}:{page-1}"))
    if end < len(jobs):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"page:{context}:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👔 Supervisor", callback_data="role:supervisor")],
        [InlineKeyboardButton(text="🔧 Subcontractor", callback_data="role:subcontractor")],
        [InlineKeyboardButton(text="👑 Admin", callback_data="role:admin")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="code_cancel")]
    ])

def get_back_keyboard(callback_data: str = "back:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data=callback_data)]
    ])

def get_decline_reason_keyboard(job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Scheduling conflict", callback_data=f"decline_reason:{job_id}:schedule")],
        [InlineKeyboardButton(text="📍 Location too far", callback_data=f"decline_reason:{job_id}:location")],
        [InlineKeyboardButton(text="💼 Too busy", callback_data=f"decline_reason:{job_id}:busy")],
        [InlineKeyboardButton(text="✍️ Custom reason", callback_data=f"decline_reason:{job_id}:custom")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data=f"view_job:sub:{job_id}")]
    ])
