from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from src.bot.database.models import UserRole, JobStatus, AvailabilityStatus

def get_main_menu_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    if role == UserRole.ADMIN:
        buttons = [
            [KeyboardButton(text="📊 Job History"), KeyboardButton(text="📦 Archive Jobs")],
            [KeyboardButton(text="🔑 Create Access Code"), KeyboardButton(text="📋 View Archived")],
            [KeyboardButton(text="👥 Manage Users"), KeyboardButton(text="🔄 Switch Role")],
            [KeyboardButton(text="ℹ️ Help"), KeyboardButton(text="📘 About")]
        ]
    elif role == UserRole.SUPERVISOR:
        buttons = [
            [KeyboardButton(text="➕ New Job"), KeyboardButton(text="📋 My Jobs")],
            [KeyboardButton(text="⏳ Pending Jobs"), KeyboardButton(text="🔄 Active Jobs")],
            [KeyboardButton(text="ℹ️ Help"), KeyboardButton(text="📘 About")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="📋 Available Jobs"), KeyboardButton(text="🔄 My Active Jobs")],
            [KeyboardButton(text="🟢 Available"), KeyboardButton(text="🟡 Busy"), KeyboardButton(text="🔴 Away")],
            [KeyboardButton(text="ℹ️ Help"), KeyboardButton(text="📘 About")]
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
        avail = "🟢" if sub.availability_status == AvailabilityStatus.AVAILABLE else "🟡" if sub.availability_status == AvailabilityStatus.BUSY else "🔴"
        buttons.append([InlineKeyboardButton(text=f"{avail} {name}", callback_data=f"assign:{sub.id}")])
    
    if include_skip:
        buttons.append([InlineKeyboardButton(text="💾 Save without sending", callback_data="assign:none")])
    
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="job_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_job_actions_keyboard(job_id: int, job_type: str = "preset", job_status: str = "sent") -> InlineKeyboardMarkup:
    buttons = []
    
    if job_status == "sent":
        if job_type == "quote":
            buttons.append([InlineKeyboardButton(text="💬 Submit Quote", callback_data=f"job_quote:{job_id}")])
        buttons.append([
            InlineKeyboardButton(text="✅ Accept", callback_data=f"job_accept:{job_id}"),
            InlineKeyboardButton(text="❌ Decline", callback_data=f"job_decline:{job_id}")
        ])
    elif job_status == "accepted":
        buttons.append([InlineKeyboardButton(text="▶️ Start Job", callback_data=f"job_start:{job_id}")])
    elif job_status == "in_progress":
        buttons.append([InlineKeyboardButton(text="✔️ Mark Complete", callback_data=f"job_complete:{job_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_supervisor_job_actions_keyboard(job_id: int, job_status: str, job_type: str = "preset") -> InlineKeyboardMarkup:
    buttons = []
    
    if job_status == "ARCHIVED":
        buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back:sup")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if job_type == "quote" and job_status in ["SENT", "CREATED"]:
        buttons.append([InlineKeyboardButton(text="📊 View Quotes", callback_data=f"view_quotes:{job_id}")])
    
    if job_status in ["CREATED", "SENT"]:
        buttons.append([InlineKeyboardButton(text="❌ Cancel Job", callback_data=f"sup_cancel:{job_id}")])
    
    if job_status in ["IN_PROGRESS", "ACCEPTED"]:
        buttons.append([InlineKeyboardButton(text="✔️ Mark Complete", callback_data=f"sup_complete:{job_id}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back:sup")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quotes_keyboard(quotes: list, job_id: int) -> InlineKeyboardMarkup:
    buttons = []
    
    for quote, user in quotes:
        name = user.first_name or user.username or f"User {user.telegram_id}"
        buttons.append([InlineKeyboardButton(
            text=f"💰 {quote.amount} - {name}",
            callback_data=f"quote_detail:{quote.id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data=f"view_job:sup:{job_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quote_detail_keyboard(quote_id: int, job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Accept This Quote", callback_data=f"accept_quote:{quote_id}")],
        [InlineKeyboardButton(text="⬅️ Back to Quotes", callback_data=f"view_quotes:{job_id}")]
    ])

def get_job_list_keyboard(jobs: list, page: int = 0, page_size: int = 5, context: str = "history") -> InlineKeyboardMarkup:
    start = page * page_size
    end = start + page_size
    page_jobs = jobs[start:end]
    
    buttons = []
    for job in page_jobs:
        status_emoji = {
            JobStatus.CREATED: "📝",
            JobStatus.SENT: "📤",
            JobStatus.ACCEPTED: "✅",
            JobStatus.IN_PROGRESS: "🔄",
            JobStatus.COMPLETED: "✔️",
            JobStatus.CANCELLED: "🚫",
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

def get_user_list_keyboard(users: list, page: int = 0, page_size: int = 5, include_self: bool = True) -> InlineKeyboardMarkup:
    start = page * page_size
    end = start + page_size
    page_users = users[start:end]
    
    buttons = []
    for user in page_users:
        role_emoji = {"admin": "👑", "supervisor": "👔", "subcontractor": "🔧"}.get(user.role.value, "👤")
        name = user.first_name or user.username or f"User {user.telegram_id}"
        buttons.append([InlineKeyboardButton(
            text=f"{role_emoji} {name}",
            callback_data=f"manage_user:{user.id}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"page:users:{page-1}"))
    if end < len(users):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"page:users:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="back:admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_user_actions_keyboard(user_id: int, is_self: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    
    if is_self:
        buttons.append([InlineKeyboardButton(text="🗑️ Delete My Account", callback_data=f"delete_user:{user_id}:self")])
    else:
        buttons.append([InlineKeyboardButton(text="🗑️ Delete User", callback_data=f"delete_user:{user_id}:other")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Back to Users", callback_data="back:users")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_switch_role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👔 Become Supervisor", callback_data="switch_role:supervisor")],
        [InlineKeyboardButton(text="🔧 Become Subcontractor", callback_data="switch_role:subcontractor")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="back:admin_menu")]
    ])

def get_confirm_delete_keyboard(user_id: int, delete_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes, Delete", callback_data=f"confirm_delete:{user_id}:{delete_type}"),
            InlineKeyboardButton(text="❌ No, Cancel", callback_data="back:users")
        ]
    ])

def get_decline_reason_keyboard(job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Scheduling conflict", callback_data=f"decline_reason:{job_id}:schedule")],
        [InlineKeyboardButton(text="📍 Location too far", callback_data=f"decline_reason:{job_id}:location")],
        [InlineKeyboardButton(text="💼 Too busy", callback_data=f"decline_reason:{job_id}:busy")],
        [InlineKeyboardButton(text="✍️ Custom reason", callback_data=f"decline_reason:{job_id}:custom")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data=f"view_job:sub:{job_id}")]
    ])

def get_availability_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Available", callback_data="avail:available")],
        [InlineKeyboardButton(text="🟡 Busy", callback_data="avail:busy")],
        [InlineKeyboardButton(text="🔴 Away", callback_data="avail:away")]
    ])
