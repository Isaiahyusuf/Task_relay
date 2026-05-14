import os
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from sqlalchemy import select

from src.bot.database import async_session, User, SafetyChecklist
from src.bot.database.models import UserRole
from src.bot.services.safety_checklist import SafetyChecklistService, SafetyChecklistPdfService


router = Router()


HAZARD_ITEMS = [
    ("Access", "Unobstructed"),
    ("Access", "Stable surface"),
    ("Access", "Clearances"),
    ("Environmental", "Traffic conditions"),
    ("Environmental", "Plant equipment nearby"),
    ("Environmental", "Waste management"),
    ("Electrical", "Overhead obstruction"),
    ("Electrical", "Live power risks"),
    ("Personnel", "Other personnel nearby"),
    ("Personnel", "General public exposure"),
]


class SafetyChecklistStates(StatesGroup):
    selecting_job = State()
    waiting_site_address = State()
    waiting_task_description = State()
    waiting_geo = State()
    waiting_hazard_status = State()
    waiting_hazard_notes = State()
    waiting_hazard_corrective = State()
    waiting_final_safe = State()
    waiting_unsafe_explanation = State()
    waiting_unsafe_photos = State()
    waiting_signature_method = State()
    waiting_typed_signature = State()
    waiting_add_workers = State()
    waiting_worker_name = State()
    waiting_worker_signature = State()
    waiting_post_task_1 = State()
    waiting_post_task_2 = State()
    waiting_post_task_3 = State()


class SafetyFilterStates(StatesGroup):
    waiting_keyword = State()


class SafetyRequestStates(StatesGroup):
    selecting_subcontractor = State()
    waiting_note = State()


def _yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="YES", callback_data=f"{prefix}:yes"),
            InlineKeyboardButton(text="NO", callback_data=f"{prefix}:no"),
        ]
    ])


def _hazard_status_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="SAFE", callback_data="haz_status:safe"),
            InlineKeyboardButton(text="UNSAFE", callback_data="haz_status:unsafe"),
        ]
    ])


def _signature_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Use Telegram username", callback_data="sig:username")],
        [InlineKeyboardButton(text="Type signature", callback_data="sig:typed")],
    ])


def _job_select_keyboard(jobs: list) -> InlineKeyboardMarkup:
    buttons = []
    for job in jobs[:12]:
        buttons.append([InlineKeyboardButton(text=f"Job #{job.id}: {job.title[:30]}", callback_data=f"safety_job:{job.id}")])
    buttons.append([InlineKeyboardButton(text="Manual entry (no job)", callback_data="safety_job:none")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _review_actions_keyboard(checklist_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Download PDF", callback_data=f"safety_pdf:{checklist_id}")],
        [
            InlineKeyboardButton(text="Approve", callback_data=f"safety_review:{checklist_id}:APPROVED"),
            InlineKeyboardButton(text="Reject", callback_data=f"safety_review:{checklist_id}:REJECTED"),
        ],
    ])


async def _get_current_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id, User.is_active == True))
        return result.scalar_one_or_none()


@router.message(F.text == "Site Safety Checklist")
async def btn_site_safety_checklist(message: Message, state: FSMContext):
    user = await _get_current_user(message.from_user.id)
    if not user or user.role != UserRole.SUBCONTRACTOR:
        await message.answer("Only subcontractors can submit site safety checklists.")
        return

    jobs = await SafetyChecklistService.get_subcontractor_active_jobs(message.from_user.id)
    has_any_request = await SafetyChecklistService.has_pending_request(user.id)
    if not has_any_request:
        await message.answer(
            "No checklist request found for you yet.\n"
            "Please wait until a manager or supervisor requests a Site Safety Checklist."
        )
        return

    await state.clear()
    await state.set_state(SafetyChecklistStates.selecting_job)
    await message.answer(
        "Site Safety Checklist\n\nSelect the related job before starting:",
        reply_markup=_job_select_keyboard(jobs),
    )


@router.callback_query(F.data.startswith("safety_job:"), StateFilter(SafetyChecklistStates.selecting_job))
async def process_selected_job(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]

    if value == "none":
        await state.update_data(job_id=None)
        await callback.message.edit_text("Enter site address:")
        await state.set_state(SafetyChecklistStates.waiting_site_address)
        await callback.answer()
        return

    job_id = int(value)
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id, User.is_active == True))
        user = result.scalar_one_or_none()
        if not user:
            await callback.answer("User not found", show_alert=True)
            return

        from src.bot.database import Job
        job_result = await session.execute(select(Job).where(Job.id == job_id, Job.subcontractor_id == user.id))
        job = job_result.scalar_one_or_none()

    if not job:
        await callback.answer("Job unavailable", show_alert=True)
        return

    has_request = await SafetyChecklistService.has_pending_request(user.id, job.id)
    if not has_request:
        await callback.answer("Checklist not requested for this job yet", show_alert=True)
        return

    await state.update_data(
        job_id=job.id,
        site_address=job.address or "",
        task_description=job.title,
    )
    await callback.message.edit_text(
        f"Selected Job #{job.id}\n\n"
        f"Current site address: {job.address or 'None'}\n"
        "Type site address or /skip to keep current:"
    )
    await state.set_state(SafetyChecklistStates.waiting_site_address)
    await callback.answer()


@router.message(StateFilter(SafetyChecklistStates.waiting_site_address))
async def process_site_address(message: Message, state: FSMContext):
    data = await state.get_data()
    text = message.text.strip()
    if text.lower() == "/skip" and data.get("site_address"):
        site_address = data["site_address"]
    else:
        site_address = text

    if not site_address:
        await message.answer("Site address is required.")
        return

    await state.update_data(site_address=site_address)

    default_task = data.get("task_description")
    if default_task:
        await message.answer(f"Current task description: {default_task}\nType new task description or /skip:")
    else:
        await message.answer("Enter job/task description:")
    await state.set_state(SafetyChecklistStates.waiting_task_description)


@router.message(StateFilter(SafetyChecklistStates.waiting_task_description))
async def process_task_description(message: Message, state: FSMContext):
    data = await state.get_data()
    text = message.text.strip()
    if text.lower() == "/skip" and data.get("task_description"):
        task_description = data["task_description"]
    else:
        task_description = text

    if not task_description:
        await message.answer("Task description is required.")
        return

    await state.update_data(task_description=task_description)
    await message.answer(
        "Send location for geo-tagging now, or type /skip.")
    await state.set_state(SafetyChecklistStates.waiting_geo)


@router.message(StateFilter(SafetyChecklistStates.waiting_geo), F.location)
async def process_geo_location(message: Message, state: FSMContext):
    geo = f"{message.location.latitude:.6f},{message.location.longitude:.6f}"
    await state.update_data(geo_location=geo)
    await state.update_data(hazard_index=0, hazard_answers=[])
    await _ask_next_hazard(message, state)


@router.message(StateFilter(SafetyChecklistStates.waiting_geo))
async def skip_geo_location(message: Message, state: FSMContext):
    if message.text.strip().lower() != "/skip":
        await message.answer("Send a location pin or type /skip.")
        return
    await state.update_data(geo_location=None)
    await state.update_data(hazard_index=0, hazard_answers=[])
    await _ask_next_hazard(message, state)


async def _ask_next_hazard(message_or_callback: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data.get("hazard_index", 0)
    if idx >= len(HAZARD_ITEMS):
        text = (
            "Final Safety Confirmation\n\n"
            "Is the site safe to complete the assigned task?"
        )
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.edit_text(text, reply_markup=_yes_no_keyboard("final_safe"))
        else:
            await message_or_callback.answer(text, reply_markup=_yes_no_keyboard("final_safe"))
        await state.set_state(SafetyChecklistStates.waiting_final_safe)
        return

    category, item = HAZARD_ITEMS[idx]
    text = (
        f"Hazard {idx + 1}/{len(HAZARD_ITEMS)}\n"
        f"Section: {category}\n"
        f"Item: {item}\n\n"
        "Select status:"
    )
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=_hazard_status_keyboard())
    else:
        await message_or_callback.answer(text, reply_markup=_hazard_status_keyboard())
    await state.set_state(SafetyChecklistStates.waiting_hazard_status)


@router.callback_query(F.data.startswith("haz_status:"), StateFilter(SafetyChecklistStates.waiting_hazard_status))
async def process_hazard_status(callback: CallbackQuery, state: FSMContext):
    status = callback.data.split(":")[1].upper()
    data = await state.get_data()
    idx = data.get("hazard_index", 0)
    category, item = HAZARD_ITEMS[idx]

    hazard_answers = data.get("hazard_answers", [])
    hazard_answers.append({
        "category": category,
        "item": item,
        "status": status,
        "notes": "",
        "corrective": "",
    })
    await state.update_data(hazard_answers=hazard_answers)
    await callback.message.edit_text(
        f"{category} / {item} = {status}\n\n"
        "Enter notes/concerns or /skip."
    )
    await state.set_state(SafetyChecklistStates.waiting_hazard_notes)
    await callback.answer()


@router.message(StateFilter(SafetyChecklistStates.waiting_hazard_notes))
async def process_hazard_notes(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    hazard_answers = data.get("hazard_answers", [])
    if not hazard_answers:
        await message.answer("Checklist state lost. Please restart checklist.")
        await state.clear()
        return

    hazard_answers[-1]["notes"] = "" if text.lower() == "/skip" else text
    await state.update_data(hazard_answers=hazard_answers)
    await message.answer("Enter corrective actions or /skip.")
    await state.set_state(SafetyChecklistStates.waiting_hazard_corrective)


@router.message(StateFilter(SafetyChecklistStates.waiting_hazard_corrective))
async def process_hazard_corrective(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    hazard_answers = data.get("hazard_answers", [])
    if not hazard_answers:
        await message.answer("Checklist state lost. Please restart checklist.")
        await state.clear()
        return

    hazard_answers[-1]["corrective"] = "" if text.lower() == "/skip" else text
    idx = data.get("hazard_index", 0) + 1
    await state.update_data(hazard_answers=hazard_answers, hazard_index=idx)
    await _ask_next_hazard(message, state)


@router.callback_query(F.data.startswith("final_safe:"), StateFilter(SafetyChecklistStates.waiting_final_safe))
async def process_final_safe(callback: CallbackQuery, state: FSMContext):
    is_safe = callback.data.endswith(":yes")
    await state.update_data(final_is_safe=is_safe)

    if is_safe:
        await callback.message.edit_text("Select signature method:", reply_markup=_signature_method_keyboard())
        await state.set_state(SafetyChecklistStates.waiting_signature_method)
    else:
        await callback.message.edit_text("Site marked unsafe. Enter explanation:")
        await state.set_state(SafetyChecklistStates.waiting_unsafe_explanation)
    await callback.answer()


@router.message(StateFilter(SafetyChecklistStates.waiting_unsafe_explanation))
async def process_unsafe_explanation(message: Message, state: FSMContext):
    explanation = message.text.strip()
    if len(explanation) < 5:
        await message.answer("Please provide a clearer explanation.")
        return

    await state.update_data(unsafe_explanation=explanation, unsafe_photos=[])
    await message.answer("Send image evidence for unsafe condition, then type /done (or /skip).")
    await state.set_state(SafetyChecklistStates.waiting_unsafe_photos)


@router.message(StateFilter(SafetyChecklistStates.waiting_unsafe_photos), F.photo)
async def process_unsafe_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("unsafe_photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(unsafe_photos=photos)
    await message.answer(f"Unsafe photo added ({len(photos)}). Send more, /done, or /skip.")


@router.message(StateFilter(SafetyChecklistStates.waiting_unsafe_photos))
async def finish_unsafe_photos(message: Message, state: FSMContext):
    cmd = message.text.strip().lower()
    if cmd not in {"/done", "/skip"}:
        await message.answer("Send photo(s), then type /done or /skip.")
        return
    await message.answer("Select signature method:", reply_markup=_signature_method_keyboard())
    await state.set_state(SafetyChecklistStates.waiting_signature_method)


@router.callback_query(F.data.startswith("sig:"), StateFilter(SafetyChecklistStates.waiting_signature_method))
async def process_signature_method(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split(":")[1]
    if method == "username":
        value = callback.from_user.username or callback.from_user.first_name or str(callback.from_user.id)
        await state.update_data(signature_type="telegram_username", signature_value=value)
        await callback.message.edit_text("Add additional worker signatures?", reply_markup=_yes_no_keyboard("workers"))
        await state.set_state(SafetyChecklistStates.waiting_add_workers)
    else:
        await callback.message.edit_text("Type your signature name:")
        await state.set_state(SafetyChecklistStates.waiting_typed_signature)
    await callback.answer()


@router.message(StateFilter(SafetyChecklistStates.waiting_typed_signature))
async def process_typed_signature(message: Message, state: FSMContext):
    signature = message.text.strip()
    if len(signature) < 2:
        await message.answer("Typed signature is too short.")
        return
    await state.update_data(signature_type="typed", signature_value=signature)
    await message.answer("Add additional worker signatures?", reply_markup=_yes_no_keyboard("workers"))
    await state.set_state(SafetyChecklistStates.waiting_add_workers)


@router.callback_query(F.data.startswith("workers:"), StateFilter(SafetyChecklistStates.waiting_add_workers))
async def process_add_workers(callback: CallbackQuery, state: FSMContext):
    if callback.data.endswith(":yes"):
        await state.update_data(workers=[])
        await callback.message.edit_text("Enter worker name (or /done to stop adding workers):")
        await state.set_state(SafetyChecklistStates.waiting_worker_name)
    else:
        await state.update_data(workers=[])
        await callback.message.edit_text("Post-task check: Waste/rubbish removed?", reply_markup=_yes_no_keyboard("post1"))
        await state.set_state(SafetyChecklistStates.waiting_post_task_1)
    await callback.answer()


@router.message(StateFilter(SafetyChecklistStates.waiting_worker_name))
async def process_worker_name(message: Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() == "/done":
        await message.answer("Post-task check: Waste/rubbish removed?", reply_markup=_yes_no_keyboard("post1"))
        await state.set_state(SafetyChecklistStates.waiting_post_task_1)
        return

    await state.update_data(current_worker_name=text)
    await message.answer("Enter this worker signature:")
    await state.set_state(SafetyChecklistStates.waiting_worker_signature)


@router.message(StateFilter(SafetyChecklistStates.waiting_worker_signature))
async def process_worker_signature(message: Message, state: FSMContext):
    signature = message.text.strip()
    data = await state.get_data()
    workers = data.get("workers", [])
    workers.append({
        "name": data.get("current_worker_name", "Worker"),
        "signature": signature,
    })
    await state.update_data(workers=workers, current_worker_name=None)
    await message.answer("Worker saved. Enter another worker name or /done.")
    await state.set_state(SafetyChecklistStates.waiting_worker_name)


@router.callback_query(F.data.startswith("post1:"), StateFilter(SafetyChecklistStates.waiting_post_task_1))
async def process_post_task_1(callback: CallbackQuery, state: FSMContext):
    await state.update_data(post_task_waste_removed=callback.data.endswith(":yes"))
    await callback.message.edit_text("Post-task check: Vehicle cleaned?", reply_markup=_yes_no_keyboard("post2"))
    await state.set_state(SafetyChecklistStates.waiting_post_task_2)
    await callback.answer()


@router.callback_query(F.data.startswith("post2:"), StateFilter(SafetyChecklistStates.waiting_post_task_2))
async def process_post_task_2(callback: CallbackQuery, state: FSMContext):
    await state.update_data(post_task_vehicle_cleaned=callback.data.endswith(":yes"))
    await callback.message.edit_text("Post-task check: Site left safe and secure?", reply_markup=_yes_no_keyboard("post3"))
    await state.set_state(SafetyChecklistStates.waiting_post_task_3)
    await callback.answer()


@router.callback_query(F.data.startswith("post3:"), StateFilter(SafetyChecklistStates.waiting_post_task_3))
async def process_post_task_3(callback: CallbackQuery, state: FSMContext):
    await state.update_data(post_task_site_secure=callback.data.endswith(":yes"))
    await callback.answer()

    user = await _get_current_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("User not found.")
        await state.clear()
        return

    data = await state.get_data()
    payload = {
        "job_id": data.get("job_id"),
        "subcontractor_id": user.id,
        "site_address": data.get("site_address"),
        "checklist_datetime": datetime.utcnow(),
        "task_description": data.get("task_description"),
        "geo_location": data.get("geo_location"),
        "hazard_answers": data.get("hazard_answers", []),
        "workers": data.get("workers", []),
        "final_is_safe": data.get("final_is_safe", True),
        "unsafe_explanation": data.get("unsafe_explanation"),
        "unsafe_photo_ids": ",".join(data.get("unsafe_photos", [])) if data.get("unsafe_photos") else None,
        "signature_type": data.get("signature_type", "typed"),
        "signature_value": data.get("signature_value", "Unknown"),
        "post_task_waste_removed": data.get("post_task_waste_removed", False),
        "post_task_vehicle_cleaned": data.get("post_task_vehicle_cleaned", False),
        "post_task_site_secure": data.get("post_task_site_secure", False),
    }

    checklist = await SafetyChecklistService.create_checklist(payload)
    if not checklist:
        await callback.message.edit_text("Failed to save checklist. Please try again.")
        await state.clear()
        return

    await SafetyChecklistService.fulfill_pending_request(
        subcontractor_id=user.id,
        checklist_id=checklist.id,
        job_id=payload.get("job_id"),
    )

    logo_path = os.path.join(os.getcwd(), "attached_assets", "company_logo.png")
    pdf_name, pdf_content = await SafetyChecklistPdfService.build_pdf(
        checklist,
        bot=callback.bot,
        company_logo_path=logo_path,
    )

    # Persist generated filename
    async with async_session() as session:
        db_result = await session.execute(select(SafetyChecklist).where(SafetyChecklist.id == checklist.id))
        db_checklist = db_result.scalar_one_or_none()
        if db_checklist:
            db_checklist.pdf_filename = pdf_name
            db_checklist.updated_at = datetime.utcnow()
            await session.commit()

    # Send to subcontractor
    await callback.message.edit_text(
        f"Checklist submitted successfully.\nChecklist ID: {checklist.id}\nStatus: PENDING"
    )
    await callback.message.answer_document(
        BufferedInputFile(pdf_content, filename=pdf_name),
        caption=f"Checklist report #{checklist.id}",
    )

    # Notify required recipients
    recipients = await SafetyChecklistService.list_notification_recipients(checklist)
    sender_name = user.first_name or user.username or f"User {user.id}"
    for recipient in recipients:
        try:
            await callback.bot.send_message(
                recipient.telegram_id,
                f"New Site Safety Checklist submitted\n"
                f"Checklist ID: {checklist.id}\n"
                f"Subcontractor: {sender_name}\n"
                f"Site: {checklist.site_address}\n"
                f"Safe to proceed: {'YES' if checklist.final_is_safe else 'NO'}",
            )
            await callback.bot.send_document(
                recipient.telegram_id,
                BufferedInputFile(pdf_content, filename=pdf_name),
                caption=f"Safety checklist #{checklist.id}",
            )
        except Exception:
            continue

    await state.clear()


@router.message(F.text == "My Submissions")
async def btn_my_submissions(message: Message):
    user = await _get_current_user(message.from_user.id)
    if not user or user.role != UserRole.SUBCONTRACTOR:
        await message.answer("Only subcontractors can access this section.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(SafetyChecklist).where(SafetyChecklist.subcontractor_id == user.id).order_by(SafetyChecklist.created_at.desc()).limit(10)
        )
        rows = list(result.scalars().all())

    if not rows:
        await message.answer("No safety checklist submissions found yet.")
        return

    text = "My Safety Submissions\n\n"
    for row in rows:
        text += (
            f"ID {row.id} | {row.status} | {row.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Site: {row.site_address}\n\n"
        )
    await message.answer(text)


@router.message(F.text == "Safety Submissions")
async def btn_safety_submissions(message: Message):
    user = await _get_current_user(message.from_user.id)
    if not user or user.role not in [UserRole.SUPERVISOR, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        await message.answer("Only supervisors and managers can review submissions.")
        return

    rows = await SafetyChecklistService.list_checklists(limit=20, status="PENDING")
    if not rows:
        await message.answer("No pending safety submissions.")
        return

    for row in rows:
        await message.answer(
            f"Checklist #{row.id}\n"
            f"Site: {row.site_address}\n"
            f"Created: {row.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Status: {row.status}",
            reply_markup=_review_actions_keyboard(row.id),
        )


@router.message(F.text == "Filter Safety Submissions")
async def btn_filter_safety_submissions(message: Message, state: FSMContext):
    user = await _get_current_user(message.from_user.id)
    if not user or user.role not in [UserRole.SUPERVISOR, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        await message.answer("Only supervisors and managers can filter submissions.")
        return

    await message.answer("Enter a keyword to filter by site or task description:")
    await state.set_state(SafetyFilterStates.waiting_keyword)


@router.message(StateFilter(SafetyFilterStates.waiting_keyword))
async def process_filter_keyword(message: Message, state: FSMContext):
    keyword = message.text.strip()
    rows = await SafetyChecklistService.list_checklists(limit=20, keyword=keyword)
    await state.clear()

    if not rows:
        await message.answer("No matching submissions found.")
        return

    for row in rows:
        await message.answer(
            f"Checklist #{row.id}\n"
            f"Site: {row.site_address}\n"
            f"Status: {row.status}\n"
            f"Created: {row.created_at.strftime('%Y-%m-%d %H:%M')}",
            reply_markup=_review_actions_keyboard(row.id),
        )


@router.callback_query(F.data.startswith("safety_pdf:"))
async def download_checklist_pdf(callback: CallbackQuery):
    checklist_id = int(callback.data.split(":")[1])
    checklist = await SafetyChecklistService.get_checklist(checklist_id)
    if not checklist:
        await callback.answer("Checklist not found", show_alert=True)
        return

    pdf_name, pdf_content = await SafetyChecklistPdfService.build_pdf(
        checklist,
        bot=callback.bot,
        company_logo_path=os.path.join(os.getcwd(), "attached_assets", "company_logo.png"),
    )
    await callback.message.answer_document(
        BufferedInputFile(pdf_content, filename=pdf_name),
        caption=f"Safety checklist #{checklist.id}",
    )
    await callback.answer("PDF sent")


@router.callback_query(F.data.startswith("safety_review:"))
async def review_checklist(callback: CallbackQuery):
    parts = callback.data.split(":")
    checklist_id = int(parts[1])
    target_status = parts[2]

    reviewer = await _get_current_user(callback.from_user.id)
    if not reviewer or reviewer.role not in [UserRole.SUPERVISOR, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        await callback.answer("Not authorized", show_alert=True)
        return

    ok = await SafetyChecklistService.update_review(
        checklist_id=checklist_id,
        reviewer_id=reviewer.id,
        status=target_status,
        comment=f"Reviewed by {reviewer.first_name or reviewer.username or reviewer.id}",
    )
    if not ok:
        await callback.answer("Unable to update review status", show_alert=True)
        return

    await callback.message.edit_text(f"Checklist #{checklist_id} marked as {target_status}")
    await callback.answer("Review saved")


@router.message(F.text == "Export Safety CSV")
async def export_safety_csv(message: Message):
    user = await _get_current_user(message.from_user.id)
    if not user or user.role not in [UserRole.SUPERVISOR, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        await message.answer("Only supervisors and managers can export reports.")
        return

    csv_text = await SafetyChecklistService.export_csv(limit=500)
    await message.answer_document(
        BufferedInputFile(csv_text.encode("utf-8"), filename="safety_checklists.csv"),
        caption="Safety checklist CSV export",
    )


@router.message(F.text == "Upload Site Photos")
async def btn_upload_site_photos(message: Message):
    await message.answer("Use Site Safety Checklist to upload unsafe-condition photos during submission.")


@router.message(F.text == "Contact Supervisor")
async def btn_contact_supervisor(message: Message):
    await message.answer("Use Send Message to contact your supervisor directly.")


def _request_subcontractor_keyboard(subcontractors: list[User]) -> InlineKeyboardMarkup:
    rows = []
    for sub in subcontractors[:20]:
        name = sub.first_name or sub.username or f"User {sub.telegram_id}"
        rows.append([InlineKeyboardButton(text=name, callback_data=f"safety_req_sub:{sub.id}")])
    rows.append([InlineKeyboardButton(text="Cancel", callback_data="safety_req_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "Request Safety Checklist")
async def btn_request_safety_checklist(message: Message, state: FSMContext):
    user = await _get_current_user(message.from_user.id)
    if not user or user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        await message.answer("Only managers and supervisors can request safety checklists.")
        return

    subs = await SafetyChecklistService.list_subcontractors_for_requester(user)
    if not subs:
        await message.answer("No subcontractors available to request from.")
        return

    await state.clear()
    await state.set_state(SafetyRequestStates.selecting_subcontractor)
    await message.answer(
        "Select subcontractor to request a Site Safety Checklist:",
        reply_markup=_request_subcontractor_keyboard(subs),
    )


@router.callback_query(F.data == "safety_req_cancel", StateFilter(SafetyRequestStates.selecting_subcontractor, SafetyRequestStates.waiting_note))
async def cancel_safety_request(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Checklist request cancelled.")
    await callback.answer()


@router.callback_query(F.data.startswith("safety_req_sub:"), StateFilter(SafetyRequestStates.selecting_subcontractor))
async def process_request_subcontractor(callback: CallbackQuery, state: FSMContext):
    sub_id = int(callback.data.split(":")[1])
    await state.update_data(request_subcontractor_id=sub_id)
    await state.set_state(SafetyRequestStates.waiting_note)
    await callback.message.edit_text(
        "Enter request note (job/task context), or type /skip:",
    )
    await callback.answer()


@router.message(StateFilter(SafetyRequestStates.waiting_note))
async def process_request_note(message: Message, state: FSMContext):
    requester = await _get_current_user(message.from_user.id)
    if not requester or requester.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        await state.clear()
        await message.answer("Not authorized.")
        return

    data = await state.get_data()
    sub_id = data.get("request_subcontractor_id")
    note = None if message.text.strip().lower() == "/skip" else message.text.strip()

    req = await SafetyChecklistService.create_request(
        requester_id=requester.id,
        subcontractor_id=sub_id,
        note=note,
    )
    if not req:
        await state.clear()
        await message.answer("Failed to create checklist request.")
        return

    # Notify subcontractor
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == sub_id))
        sub = result.scalar_one_or_none()

    if sub and sub.telegram_id:
        requester_name = requester.first_name or requester.username or "Manager"
        try:
            await message.bot.send_message(
                sub.telegram_id,
                f"Site Safety Checklist requested by {requester_name}.\n"
                f"Please open 'Site Safety Checklist' and complete it before starting work.\n"
                f"Note: {note or 'No note provided.'}"
            )
        except Exception:
            pass

    await state.clear()
    await message.answer("Checklist request sent to subcontractor.")

