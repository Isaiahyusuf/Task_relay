import json
import os
import tempfile
from datetime import datetime, date
from io import StringIO
from typing import Any

from fpdf import FPDF
from sqlalchemy import select, or_, func
from sqlalchemy.exc import SQLAlchemyError

from src.bot.database import async_session, SafetyChecklist, SafetyChecklistAudit, SafetyChecklistRequest, User, Job
from src.bot.database.models import UserRole, JobStatus


class SafetyChecklistService:
    @staticmethod
    async def log_action(checklist_id: int, actor_id: int | None, action: str, details: str | None = None):
        if not async_session:
            return
        async with async_session() as session:
            audit = SafetyChecklistAudit(
                checklist_id=checklist_id,
                actor_id=actor_id,
                action=action,
                details=details,
            )
            session.add(audit)
            await session.commit()

    @staticmethod
    async def get_user_by_tg(telegram_id: int) -> User | None:
        if not async_session:
            return None
        async with async_session() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id, User.is_active == True))
            return result.scalar_one_or_none()

    @staticmethod
    async def get_subcontractor_active_jobs(telegram_id: int) -> list[Job]:
        if not async_session:
            return []
        async with async_session() as session:
            user_result = await session.execute(select(User).where(User.telegram_id == telegram_id, User.is_active == True))
            user = user_result.scalar_one_or_none()
            if not user:
                return []
            jobs_result = await session.execute(
                select(Job).where(
                    Job.subcontractor_id == user.id,
                    Job.status.in_([JobStatus.ACCEPTED, JobStatus.IN_PROGRESS, JobStatus.SUBMITTED])
                ).order_by(Job.created_at.desc())
            )
            return list(jobs_result.scalars().all())

    @staticmethod
    async def has_submitted_for_job_today(job_id: int, subcontractor_id: int) -> bool:
        if not async_session:
            return False
        day_start = datetime.combine(date.today(), datetime.min.time())
        async with async_session() as session:
            result = await session.execute(
                select(func.count(SafetyChecklist.id)).where(
                    SafetyChecklist.job_id == job_id,
                    SafetyChecklist.subcontractor_id == subcontractor_id,
                    SafetyChecklist.created_at >= day_start,
                )
            )
            return (result.scalar() or 0) > 0

    @staticmethod
    async def create_request(requester_id: int, subcontractor_id: int, job_id: int | None = None, note: str | None = None) -> SafetyChecklistRequest | None:
        if not async_session:
            return None
        async with async_session() as session:
            try:
                req = SafetyChecklistRequest(
                    requester_id=requester_id,
                    subcontractor_id=subcontractor_id,
                    job_id=job_id,
                    note=note,
                    status="PENDING",
                    requested_at=datetime.utcnow(),
                )
                session.add(req)
                await session.commit()
                await session.refresh(req)
                return req
            except SQLAlchemyError:
                await session.rollback()
                return None

    @staticmethod
    async def has_pending_request(subcontractor_id: int, job_id: int | None = None) -> bool:
        if not async_session:
            return False
        async with async_session() as session:
            q = select(func.count(SafetyChecklistRequest.id)).where(
                SafetyChecklistRequest.subcontractor_id == subcontractor_id,
                SafetyChecklistRequest.status == "PENDING",
            )
            if job_id is not None:
                q = q.where(or_(SafetyChecklistRequest.job_id == job_id, SafetyChecklistRequest.job_id == None))
            result = await session.execute(q)
            return (result.scalar() or 0) > 0

    @staticmethod
    async def fulfill_pending_request(subcontractor_id: int, checklist_id: int, job_id: int | None = None):
        if not async_session:
            return
        async with async_session() as session:
            q = select(SafetyChecklistRequest).where(
                SafetyChecklistRequest.subcontractor_id == subcontractor_id,
                SafetyChecklistRequest.status == "PENDING",
            ).order_by(SafetyChecklistRequest.requested_at.asc())
            if job_id is not None:
                q = q.where(or_(SafetyChecklistRequest.job_id == job_id, SafetyChecklistRequest.job_id == None))

            result = await session.execute(q)
            req = result.scalar_one_or_none()
            if not req:
                return
            req.status = "FULFILLED"
            req.checklist_id = checklist_id
            req.fulfilled_at = datetime.utcnow()
            await session.commit()

    @staticmethod
    async def list_subcontractors_for_requester(requester: User) -> list[User]:
        if not async_session:
            return []
        async with async_session() as session:
            q = select(User).where(User.role == UserRole.SUBCONTRACTOR, User.is_active == True)
            if requester.role == UserRole.SUPERVISOR and requester.team_id:
                q = q.where(User.team_id == requester.team_id)
            q = q.order_by(User.first_name)
            result = await session.execute(q)
            return list(result.scalars().all())

    @staticmethod
    async def list_subcontractor_checklists(subcontractor_id: int, limit: int = 10) -> list[SafetyChecklist]:
        if not async_session:
            return []
        async with async_session() as session:
            result = await session.execute(
                select(SafetyChecklist).where(
                    SafetyChecklist.subcontractor_id == subcontractor_id
                ).order_by(SafetyChecklist.created_at.desc()).limit(limit)
            )
            return list(result.scalars().all())

    @staticmethod
    async def create_checklist(payload: dict[str, Any]) -> SafetyChecklist | None:
        if not async_session:
            return None
        now = datetime.utcnow()
        async with async_session() as session:
            checklist = SafetyChecklist(
                job_id=payload.get("job_id"),
                subcontractor_id=payload["subcontractor_id"],
                site_address=payload["site_address"],
                checklist_datetime=payload.get("checklist_datetime") or now,
                task_description=payload["task_description"],
                geo_location=payload.get("geo_location"),
                hazard_answers_json=json.dumps(payload.get("hazard_answers", []), ensure_ascii=True),
                worker_signatures_json=json.dumps(payload.get("workers", []), ensure_ascii=True),
                final_is_safe=payload["final_is_safe"],
                unsafe_explanation=payload.get("unsafe_explanation"),
                unsafe_photo_ids=payload.get("unsafe_photo_ids"),
                signature_type=payload["signature_type"],
                signature_value=payload["signature_value"],
                post_task_waste_removed=payload.get("post_task_waste_removed", False),
                post_task_vehicle_cleaned=payload.get("post_task_vehicle_cleaned", False),
                post_task_site_secure=payload.get("post_task_site_secure", False),
                status="PENDING",
                created_at=now,
                updated_at=now,
            )
            session.add(checklist)
            await session.commit()
            await session.refresh(checklist)

            audit = SafetyChecklistAudit(
                checklist_id=checklist.id,
                actor_id=payload["subcontractor_id"],
                action="SUBMITTED",
                details=f"Checklist submitted for site: {checklist.site_address}",
            )
            session.add(audit)
            await session.commit()
            return checklist

    @staticmethod
    async def get_checklist(checklist_id: int) -> SafetyChecklist | None:
        if not async_session:
            return None
        async with async_session() as session:
            result = await session.execute(select(SafetyChecklist).where(SafetyChecklist.id == checklist_id))
            return result.scalar_one_or_none()

    @staticmethod
    async def list_checklists(limit: int = 30, status: str | None = None, keyword: str | None = None) -> list[SafetyChecklist]:
        if not async_session:
            return []
        async with async_session() as session:
            q = select(SafetyChecklist).order_by(SafetyChecklist.created_at.desc()).limit(limit)
            if status:
                q = q.where(SafetyChecklist.status == status.upper())
            if keyword:
                like = f"%{keyword}%"
                q = q.where(
                    or_(
                        SafetyChecklist.site_address.ilike(like),
                        SafetyChecklist.task_description.ilike(like),
                    )
                )
            result = await session.execute(q)
            return list(result.scalars().all())

    @staticmethod
    async def update_review(checklist_id: int, reviewer_id: int, status: str, comment: str | None = None) -> bool:
        if not async_session:
            return False
        status = status.upper()
        if status not in {"APPROVED", "REJECTED"}:
            return False

        async with async_session() as session:
            result = await session.execute(select(SafetyChecklist).where(SafetyChecklist.id == checklist_id))
            checklist = result.scalar_one_or_none()
            if not checklist:
                return False

            checklist.status = status
            checklist.reviewed_by_id = reviewer_id
            checklist.reviewed_at = datetime.utcnow()
            checklist.review_comment = comment
            checklist.updated_at = datetime.utcnow()

            audit = SafetyChecklistAudit(
                checklist_id=checklist_id,
                actor_id=reviewer_id,
                action=status,
                details=comment,
            )
            session.add(audit)
            await session.commit()
            return True

    @staticmethod
    async def list_notification_recipients(checklist: SafetyChecklist) -> list[User]:
        if not async_session:
            return []
        async with async_session() as session:
            recipients: dict[int, User] = {}

            # Assigned supervisor for the job
            if checklist.job_id:
                job_result = await session.execute(select(Job).where(Job.id == checklist.job_id))
                job = job_result.scalar_one_or_none()
                if job and job.supervisor_id:
                    sup_result = await session.execute(select(User).where(User.id == job.supervisor_id, User.is_active == True))
                    supervisor = sup_result.scalar_one_or_none()
                    if supervisor and supervisor.telegram_id:
                        recipients[supervisor.id] = supervisor

            # General Manager + Managers
            mgr_result = await session.execute(
                select(User).where(
                    User.is_active == True,
                    User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN]),
                )
            )
            for user in mgr_result.scalars().all():
                if user.telegram_id:
                    recipients[user.id] = user

            # Remove checklist owner from recipients
            recipients.pop(checklist.subcontractor_id, None)
            return list(recipients.values())

    @staticmethod
    async def export_csv(limit: int = 100) -> str:
        checklists = await SafetyChecklistService.list_checklists(limit=limit)
        buffer = StringIO()
        buffer.write(
            "id,created_at,status,site_address,task_description,subcontractor_id,job_id,final_is_safe,reviewed_at\n"
        )
        for c in checklists:
            line = (
                f"{c.id},{c.created_at},{c.status},\"{(c.site_address or '').replace(chr(34), chr(39))}\","
                f"\"{(c.task_description or '').replace(chr(34), chr(39))}\",{c.subcontractor_id},{c.job_id or ''},"
                f"{c.final_is_safe},{c.reviewed_at or ''}\n"
            )
            buffer.write(line)
        return buffer.getvalue()


class SafetyChecklistPdfService:
    @staticmethod
    def _safe(value: str | None) -> str:
        if value is None:
            return "N/A"
        return str(value).encode("latin-1", errors="replace").decode("latin-1")

    @staticmethod
    async def _download_temp_photo(bot: Any, file_id: str) -> str:
        tg_file = await bot.get_file(file_id)
        downloaded = await bot.download_file(tg_file.file_path)

        if hasattr(downloaded, "seek"):
            downloaded.seek(0)
        data = downloaded.read()

        suffix = os.path.splitext(tg_file.file_path or "")[1].lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(data)
            return temp_file.name

    @classmethod
    async def build_pdf(
        cls,
        checklist: SafetyChecklist,
        bot: Any | None = None,
        company_logo_path: str | None = None,
    ) -> tuple[str, bytes]:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        if company_logo_path and os.path.exists(company_logo_path):
            try:
                pdf.image(company_logo_path, x=10, y=8, w=32)
                pdf.ln(20)
            except Exception:
                pdf.ln(4)

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Site Safety Checklist", ln=True)
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 8, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"Checklist ID: {checklist.id}", ln=True)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 7, f"Site Address: {cls._safe(checklist.site_address)}")
        pdf.multi_cell(0, 7, f"Date Time: {checklist.checklist_datetime.strftime('%Y-%m-%d %H:%M')}")
        pdf.multi_cell(0, 7, f"Task Description: {cls._safe(checklist.task_description)}")
        pdf.multi_cell(0, 7, f"Final Site Safe: {'YES' if checklist.final_is_safe else 'NO'}")
        pdf.multi_cell(0, 7, f"Signature: {cls._safe(checklist.signature_type)} - {cls._safe(checklist.signature_value)}")
        if checklist.geo_location:
            pdf.multi_cell(0, 7, f"Geo Location: {checklist.geo_location}")
        pdf.ln(2)

        hazard_answers = []
        workers = []
        try:
            hazard_answers = json.loads(checklist.hazard_answers_json or "[]")
            workers = json.loads(checklist.worker_signatures_json or "[]")
        except Exception:
            pass

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Hazard Assessment", ln=True)
        for item in hazard_answers:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, f"{cls._safe(item.get('category'))} / {cls._safe(item.get('item'))}: {cls._safe(item.get('status'))}")
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 6, f"Notes: {cls._safe(item.get('notes') or 'None')}")
            pdf.multi_cell(0, 6, f"Corrective Action: {cls._safe(item.get('corrective') or 'None')}")
            pdf.ln(1)

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Worker Signatures", ln=True)
        pdf.set_font("Helvetica", size=10)
        if workers:
            for worker in workers:
                pdf.multi_cell(0, 6, f"{cls._safe(worker.get('name'))} - {cls._safe(worker.get('signature'))}")
        else:
            pdf.multi_cell(0, 6, "No additional workers listed")

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Post Task Checklist", ln=True)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 6, f"Waste removed: {'YES' if checklist.post_task_waste_removed else 'NO'}")
        pdf.multi_cell(0, 6, f"Vehicle cleaned: {'YES' if checklist.post_task_vehicle_cleaned else 'NO'}")
        pdf.multi_cell(0, 6, f"Site safe and secure: {'YES' if checklist.post_task_site_secure else 'NO'}")

        if checklist.unsafe_explanation:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Unsafe Explanation", ln=True)
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 6, cls._safe(checklist.unsafe_explanation))

        # Embed unsafe photos if provided
        if bot and checklist.unsafe_photo_ids:
            photo_ids = [p.strip() for p in checklist.unsafe_photo_ids.split(",") if p.strip()][:5]
            if photo_ids:
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, "Attached Photos", ln=True)
            for idx, photo_id in enumerate(photo_ids, start=1):
                temp_path = None
                try:
                    temp_path = await cls._download_temp_photo(bot, photo_id)
                    pdf.set_font("Helvetica", size=10)
                    pdf.cell(0, 7, f"Photo {idx}", ln=True)
                    page_width = pdf.w - pdf.l_margin - pdf.r_margin
                    pdf.image(temp_path, w=page_width)
                    pdf.ln(2)
                except Exception:
                    continue
                finally:
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except OSError:
                            pass

        out = pdf.output(dest="S")
        content = out.encode("latin-1") if isinstance(out, str) else bytes(out)
        filename = f"safety_checklist_{checklist.id}.pdf"
        return filename, content
