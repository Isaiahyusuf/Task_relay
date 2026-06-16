from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from src.bot.database.models import UserRole, JobStatus, AvailabilityStatus
from src.bot.utils.roles import creatable_roles

def get_main_menu_keyboard(role: UserRole, lang: str = "en") -> ReplyKeyboardMarkup:
    from src.bot.i18n import get_text as t
    if role == UserRole.SUPER_ADMIN:
        buttons = [
            [KeyboardButton(text=t("Job History", lang)), KeyboardButton(text=t("Archive Jobs", lang))],
            [KeyboardButton(text=t("Send Message", lang))],
            [KeyboardButton(text=t("Safety Submissions", lang)), KeyboardButton(text=t("Filter Safety Submissions", lang))],
            [KeyboardButton(text=t("Export Safety CSV", lang))],
            [KeyboardButton(text=t("All Access Codes", lang))],
            [KeyboardButton(text=t("Manage Access Codes", lang))],
            [KeyboardButton(text=t("Create Manager Code", lang)), KeyboardButton(text=t("Create Supervisor Code", lang))],
            [KeyboardButton(text=t("Create Subcontractor Code", lang))],
            [KeyboardButton(text=t("View By Teams", lang)), KeyboardButton(text=t("View Regions", lang))],
            [KeyboardButton(text=t("Manage Roles", lang)), KeyboardButton(text=t("Manage Regions", lang))],
            [KeyboardButton(text=t("Manage Teams", lang))],
            [KeyboardButton(text=t("View Managers", lang)), KeyboardButton(text=t("View Supervisors", lang))],
            [KeyboardButton(text=t("View Subcontractors", lang)), KeyboardButton(text=t("All Users", lang))],
            [KeyboardButton(text=t("Switch Role", lang)), KeyboardButton(text=t("View Archived", lang))],
            [KeyboardButton(text=t("Help", lang)), KeyboardButton(text=t("About", lang))],
            [KeyboardButton(text=t("Language", lang))],
        ]
    elif role == UserRole.ADMIN:
        buttons = [
            [KeyboardButton(text=t("Job History", lang)), KeyboardButton(text=t("Archive Jobs", lang))],
            [KeyboardButton(text=t("New Job", lang)), KeyboardButton(text=t("Send Message", lang))],
            [KeyboardButton(text=t("Request Availability", lang))],
            [KeyboardButton(text=t("Request Safety Checklist", lang))],
            [KeyboardButton(text=t("Safety Submissions", lang)), KeyboardButton(text=t("Filter Safety Submissions", lang))],
            [KeyboardButton(text=t("Export Safety CSV", lang))],
            [KeyboardButton(text=t("Weekly Availability", lang))],
            [KeyboardButton(text=t("Manage Access Codes", lang))],
            [KeyboardButton(text=t("Create Access Code", lang)), KeyboardButton(text=t("View Archived", lang))],
            [KeyboardButton(text=t("View By Teams", lang)), KeyboardButton(text=t("View Regions", lang))],
            [KeyboardButton(text=t("Manage Teams", lang)), KeyboardButton(text=t("Manage Regions", lang))],
            [KeyboardButton(text=t("Manage Users", lang))],
            [KeyboardButton(text=t("Switch Role", lang))],
            [KeyboardButton(text=t("Help", lang)), KeyboardButton(text=t("About", lang))],
            [KeyboardButton(text=t("Language", lang))],
        ]
    elif role == UserRole.SUPERVISOR:
        buttons = [
            [KeyboardButton(text=t("New Job", lang)), KeyboardButton(text=t("My Jobs", lang))],
            [KeyboardButton(text=t("Pending Jobs", lang)), KeyboardButton(text=t("Active Jobs", lang))],
            [KeyboardButton(text=t("Submitted Jobs", lang))],
            [KeyboardButton(text=t("Request Safety Checklist", lang))],
            [KeyboardButton(text=t("Safety Submissions", lang)), KeyboardButton(text=t("Filter Safety Submissions", lang))],
            [KeyboardButton(text=t("Export Safety CSV", lang))],
            [KeyboardButton(text=t("Manage Access Codes", lang))],
            [KeyboardButton(text=t("Send Message", lang)), KeyboardButton(text=t("Create Subcontractor Code", lang))],
            [KeyboardButton(text=t("Help", lang)), KeyboardButton(text=t("About", lang))],
            [KeyboardButton(text=t("Language", lang))],
            [KeyboardButton(text=t("Delete My Account", lang))],
        ]
    else:
        buttons = [
            [KeyboardButton(text=t("Available Jobs", lang)), KeyboardButton(text=t("My Active Jobs", lang))],
            [KeyboardButton(text=t("Start Work", lang)), KeyboardButton(text=t("Site Safety Checklist", lang))],
            [KeyboardButton(text=t("Upload Site Photos", lang)), KeyboardButton(text=t("My Submissions", lang))],
            [KeyboardButton(text=t("Submit Job", lang)), KeyboardButton(text=t("My Availability", lang))],
            [KeyboardButton(text=t("Report Unavailability", lang))],
            [KeyboardButton(text=t("Available", lang)), KeyboardButton(text=t("Busy", lang)), KeyboardButton(text=t("Away", lang))],
            [KeyboardButton(text=t("Help", lang)), KeyboardButton(text=t("About", lang))],
            [KeyboardButton(text=t("Language", lang))],
            [KeyboardButton(text=t("Delete My Account", lang))],
        ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_job_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Quote Job", callback_data="job_type:quote")],
        [InlineKeyboardButton(text="Preset Price Job", callback_data="job_type:preset")],
        [InlineKeyboardButton(text="Cancel", callback_data="job_cancel")]
    ])

def get_skip_keyboard(field: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Skip", callback_data=f"skip:{field}")],
        [InlineKeyboardButton(text="Cancel", callback_data="job_cancel")]
    ])

def get_confirmation_keyboard(action: str, item_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Confirm", callback_data=f"confirm:{action}:{item_id}"),
            InlineKeyboardButton(text="Cancel", callback_data=f"cancel:{action}:{item_id}")
        ]
    ])

def get_team_selection_keyboard(for_code: bool = False) -> InlineKeyboardMarkup:
    prefix = "code_team" if for_code else "job_team"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="North/West subcontractors", callback_data=f"{prefix}:northwest")],
        [InlineKeyboardButton(text="South/East subcontractors", callback_data=f"{prefix}:southeast")],
        [InlineKeyboardButton(text="Cancel", callback_data="cancel_code" if for_code else "job_cancel")]
    ])

def get_job_team_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Send Bot-Wide (All Teams)", callback_data="job_send:all")],
        [InlineKeyboardButton(text="North/West Only", callback_data="job_send:northwest")],
        [InlineKeyboardButton(text="South/East Only", callback_data="job_send:southeast")],
        [InlineKeyboardButton(text="Save as Draft", callback_data="job_send:draft")],
        [InlineKeyboardButton(text="Cancel", callback_data="job_cancel")]
    ])

def get_subcontractor_selection_keyboard(subcontractors: list, include_skip: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    
    # Add "Send to All" option at the top
    if subcontractors:
        buttons.append([InlineKeyboardButton(text="Send to All Available ✅", callback_data="assign:all")])
    
    for sub in subcontractors:
        name = sub.first_name or sub.username or f"User {sub.telegram_id}"
        if sub.availability_status == AvailabilityStatus.AVAILABLE:
            avail = "[AVAILABLE]"
        elif sub.availability_status == AvailabilityStatus.BUSY:
            avail = "[BUSY]"
        else:
            avail = "[AWAY]"
        buttons.append([InlineKeyboardButton(text=f"{avail} {name}", callback_data=f"assign:{sub.id}")])
    
    if include_skip:
        buttons.append([InlineKeyboardButton(text="Save without sending 📌", callback_data="assign:none")])
    
    buttons.append([InlineKeyboardButton(text="Cancel ✖", callback_data="job_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_job_actions_keyboard(job_id: int, job_type: str = "preset", job_status: str = "sent") -> InlineKeyboardMarkup:
    buttons = []
    
    status_lower = job_status.lower() if job_status else ""
    
    if status_lower == "sent":
        if job_type == "quote":
            buttons.append([InlineKeyboardButton(text="Submit Quote", callback_data=f"job_quote:{job_id}")])
        buttons.append([
            InlineKeyboardButton(text="Accept", callback_data=f"job_accept:{job_id}"),
            InlineKeyboardButton(text="Decline", callback_data=f"job_decline:{job_id}")
        ])
    elif status_lower == "accepted":
        buttons.append([InlineKeyboardButton(text="Start Job", callback_data=f"job_start:{job_id}")])
    elif status_lower == "in_progress":
        buttons.append([InlineKeyboardButton(text="Submit Job", callback_data=f"job_submit:{job_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_supervisor_job_actions_keyboard(job_id: int, job_status: str, job_type: str = "preset", is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    
    if job_status == "ARCHIVED" and not is_admin:
        buttons.append([InlineKeyboardButton(text="Back", callback_data="back:sup")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if is_admin:
        buttons.append([InlineKeyboardButton(text="Delete Job", callback_data=f"admin_delete_job:{job_id}")])

    if job_type == "quote" and job_status in ["SENT", "CREATED"]:
        buttons.append([InlineKeyboardButton(text="View Quotes", callback_data=f"view_quotes:{job_id}")])
    
    if job_status in ["CREATED", "SENT"]:
        buttons.append([InlineKeyboardButton(text="Cancel Job", callback_data=f"sup_cancel:{job_id}")])
    
    if job_status == "SUBMITTED":
        buttons.append([InlineKeyboardButton(text="View Submission", callback_data=f"view_submission:{job_id}")])
        buttons.append([InlineKeyboardButton(text="Mark Complete", callback_data=f"sup_complete:{job_id}")])
        buttons.append([InlineKeyboardButton(text="Not Satisfied", callback_data=f"sup_not_satisfied:{job_id}")])
    
    back_callback = "back:history" if is_admin else "back:sup"
    buttons.append([InlineKeyboardButton(text="Back", callback_data=back_callback)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quotes_keyboard(quotes: list, job_id: int) -> InlineKeyboardMarkup:
    buttons = []
    
    for quote, user in quotes:
        name = user.first_name or user.username or f"User {user.telegram_id}"
        buttons.append([InlineKeyboardButton(
            text=f" {quote.amount} - {name}",
            callback_data=f"quote_detail:{quote.id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="Back", callback_data=f"view_job:sup:{job_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quote_detail_keyboard(quote_id: int, job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Accept This Quote", callback_data=f"accept_quote:{quote_id}")],
        [InlineKeyboardButton(text="Decline Quote", callback_data=f"decline_quote:{quote_id}")],
        [InlineKeyboardButton(text="Back to Quotes", callback_data=f"view_quotes:{job_id}")]
    ])

def get_job_list_keyboard(jobs: list, page: int = 0, page_size: int = 5, context: str = "history") -> InlineKeyboardMarkup:
    start = page * page_size
    end = start + page_size
    page_jobs = jobs[start:end]
    
    buttons = []
    for job in page_jobs:
        status_emoji = {
            JobStatus.CREATED: "",
            JobStatus.SENT: "",
            JobStatus.ACCEPTED: "",
            JobStatus.IN_PROGRESS: "",
            JobStatus.SUBMITTED: "",
            JobStatus.COMPLETED: "",
            JobStatus.CANCELLED: "",
            JobStatus.ARCHIVED: ""
        }.get(job.status, "")
        
        buttons.append([InlineKeyboardButton(
            text=f"{status_emoji} #{job.id}: {job.title[:30]}",
            callback_data=f"view_job:{context}:{job.id}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Previous", callback_data=f"page:{context}:{page-1}"))
    if end < len(jobs):
        nav_buttons.append(InlineKeyboardButton(text="Next", callback_data=f"page:{context}:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_role_selection_keyboard(creator_role: str = "super_admin") -> InlineKeyboardMarkup:
    """
    Returns role options based on hierarchy:
    - Super Admin: can create Admin, Supervisor, Subcontractor codes
    - Admin: can create Supervisor, Subcontractor codes
    - Supervisor: can create Subcontractor codes only
    """
    buttons = []

    role_map = {
        "super_admin": UserRole.SUPER_ADMIN,
        "admin": UserRole.ADMIN,
        "supervisor": UserRole.SUPERVISOR,
        "subcontractor": UserRole.SUBCONTRACTOR,
    }
    role_options = creatable_roles(role_map.get(creator_role))

    labels = {
        UserRole.ADMIN: " Manager",
        UserRole.SUPERVISOR: " Supervisor",
        UserRole.SUBCONTRACTOR: " Subcontractor",
    }

    for role in role_options:
        buttons.append([InlineKeyboardButton(text=labels[role], callback_data=f"role:{role.value}")])
    
    buttons.append([InlineKeyboardButton(text="Cancel", callback_data="code_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_keyboard(callback_data: str = "back:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data=callback_data)]
    ])

def get_user_list_keyboard(users: list, page: int = 0, page_size: int = 5, include_self: bool = True, is_super_admin: bool = False) -> InlineKeyboardMarkup:
    start = page * page_size
    end = start + page_size
    page_users = users[start:end]
    
    buttons = []
    for user in page_users:
        role_emoji = {"admin": "", "supervisor": "", "subcontractor": ""}.get(user.role.value, "")
        name = user.first_name or user.username or f"User {user.telegram_id}"
        buttons.append([InlineKeyboardButton(
            text=f"{role_emoji} {name}",
            callback_data=f"manage_user:{user.id}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Previous", callback_data=f"page:users:{page-1}"))
    if end < len(users):
        nav_buttons.append(InlineKeyboardButton(text="Next", callback_data=f"page:users:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="Back", callback_data="back:admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_user_actions_keyboard(user_id: int, is_self: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    
    if is_self:
        buttons.append([InlineKeyboardButton(text="Delete My Account", callback_data=f"delete_user:{user_id}:self")])
    else:
        buttons.append([InlineKeyboardButton(text="Delete User", callback_data=f"delete_user:{user_id}:other")])
    
    buttons.append([InlineKeyboardButton(text="Back to Users", callback_data="back:users")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_switch_role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Become Supervisor", callback_data="switch_role:supervisor")],
        [InlineKeyboardButton(text="Become Subcontractor", callback_data="switch_role:subcontractor")],
        [InlineKeyboardButton(text="Cancel", callback_data="back:admin_menu")]
    ])

def get_super_admin_switch_role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Manager", callback_data="sa_switch:admin")],
        [InlineKeyboardButton(text="Supervisor", callback_data="sa_switch:supervisor")],
        [InlineKeyboardButton(text="Subcontractor", callback_data="sa_switch:subcontractor")],
        [InlineKeyboardButton(text="Cancel", callback_data="back:sa_menu")]
    ])

def get_confirm_delete_keyboard(user_id: int, delete_type: str) -> InlineKeyboardMarkup:
    cancel_callback = "back:users" if delete_type == "other" else "cancel_self_delete"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes, Delete", callback_data=f"confirm_delete:{user_id}:{delete_type}"),
            InlineKeyboardButton(text="No, Cancel", callback_data=cancel_callback)
        ]
    ])

def get_self_delete_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes, Delete My Account", callback_data=f"confirm_self_delete:{user_id}"),
            InlineKeyboardButton(text="No, Cancel", callback_data="cancel_self_delete")
        ]
    ])

def get_confirm_job_delete_keyboard(job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes, Delete Job", callback_data=f"confirm_job_delete:{job_id}"),
            InlineKeyboardButton(text="No, Cancel", callback_data=f"view_job:history:{job_id}")
        ]
    ])

def get_decline_reason_keyboard(job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Scheduling conflict", callback_data=f"decline_reason:{job_id}:schedule")],
        [InlineKeyboardButton(text="Location too far", callback_data=f"decline_reason:{job_id}:location")],
        [InlineKeyboardButton(text="Too busy", callback_data=f"decline_reason:{job_id}:busy")],
        [InlineKeyboardButton(text="Custom reason", callback_data=f"decline_reason:{job_id}:custom")],
        [InlineKeyboardButton(text="Back", callback_data=f"view_job:sub:{job_id}")]
    ])

def get_availability_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Available", callback_data="avail:available")],
        [InlineKeyboardButton(text="Busy", callback_data="avail:busy")],
        [InlineKeyboardButton(text="Away", callback_data="avail:away")]
    ])

def get_weekly_availability_keyboard(week_id: int, selected_days: list = None) -> InlineKeyboardMarkup:
    selected_days = selected_days or []
    days = [
        ("Monday", "mon"),
        ("Tuesday", "tue"),
        ("Wednesday", "wed"),
        ("Thursday", "thu"),
        ("Friday", "fri")
    ]
    buttons = []
    for day_name, day_code in days:
        check = "☑" if day_code in selected_days else "☐"
        buttons.append([InlineKeyboardButton(
            text=f"{check} {day_name}",
            callback_data=f"weekly_avail:{week_id}:toggle:{day_code}"
        )])
    buttons.append([InlineKeyboardButton(text="Save Availability ✅", callback_data=f"weekly_avail:{week_id}:save")])
    buttons.append([InlineKeyboardButton(text="Add Notes 📝", callback_data=f"weekly_avail:{week_id}:notes")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_supervisor_availability_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="View Subcontractor Availability", callback_data="sup_view_avail")],
        [InlineKeyboardButton(text="Back", callback_data="back_main")]
    ])

def get_message_target_keyboard(sender_role: UserRole | None = None) -> InlineKeyboardMarkup:
    rows = []
    if sender_role == UserRole.SUPER_ADMIN:
        rows.append([InlineKeyboardButton(text="Everyone on Bot 🌐", callback_data="msg_target:all_users")])
    rows.extend([
        [InlineKeyboardButton(text="All Subcontractors 👷", callback_data="msg_target:all_subs")],
        [InlineKeyboardButton(text="North/West Team 🧭", callback_data="msg_target:northwest")],
        [InlineKeyboardButton(text="South/East Team 🗺", callback_data="msg_target:southeast")],
        [InlineKeyboardButton(text="Select Specific Users ☑", callback_data="msg_target:select")],
        [InlineKeyboardButton(text="Cancel ✖", callback_data="msg_cancel")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_subcontractor_select_keyboard(subcontractors: list, selected_ids: list = None) -> InlineKeyboardMarkup:
    selected_ids = selected_ids or []
    buttons = []
    
    for sub in subcontractors:
        name = sub.first_name or sub.username or f"User {sub.telegram_id}"
        check = "☑" if sub.id in selected_ids else "☐"
        buttons.append([InlineKeyboardButton(
            text=f"{check} {name}",
            callback_data=f"msg_select:{sub.id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="Send Message ✅", callback_data="msg_send")])
    buttons.append([InlineKeyboardButton(text="Cancel ✖", callback_data="msg_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_availability_request_select_keyboard(subcontractors: list, selected_ids: list = None) -> InlineKeyboardMarkup:
    selected_ids = selected_ids or []
    buttons = []

    for sub in subcontractors:
        name = sub.first_name or sub.username or f"User {sub.telegram_id}"
        check = "☑" if sub.id in selected_ids else "☐"
        buttons.append([InlineKeyboardButton(
            text=f"{check} {name}",
            callback_data=f"avail_req_select:{sub.id}"
        )])

    buttons.append([InlineKeyboardButton(text="Request Availability ✅", callback_data="avail_req_send")])
    buttons.append([InlineKeyboardButton(text="Cancel ✖", callback_data="avail_req_cancel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_unavailability_job_keyboard(jobs: list) -> InlineKeyboardMarkup:
    buttons = []
    
    for job in jobs:
        buttons.append([InlineKeyboardButton(
            text=f"#{job.id}: {job.title[:30]}",
            callback_data=f"unavail_job:{job.id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="General Unavailability", callback_data="unavail_job:general")])
    buttons.append([InlineKeyboardButton(text="Cancel", callback_data="unavail_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_skip_photos_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Skip Photos", callback_data="skip:photos")],
        [InlineKeyboardButton(text="Cancel", callback_data="job_cancel")]
    ])

def get_skip_deadline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="No Deadline", callback_data="skip:deadline")],
        [InlineKeyboardButton(text="Cancel", callback_data="job_cancel")]
    ])

def get_unavailability_response_keyboard(notice_id: int, subcontractor_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Send Feedback", callback_data=f"unavail_feedback:{notice_id}:{subcontractor_id}")],
        [InlineKeyboardButton(text="Acknowledged", callback_data=f"unavail_ack:{notice_id}")]
    ])

def get_message_reaction_keyboard(broadcast_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Acknowledge", callback_data=f"msg_ack:{broadcast_id}")],
        [InlineKeyboardButton(text="Reply", callback_data=f"msg_reply:{broadcast_id}")]
    ])


