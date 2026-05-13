from datetime import datetime
import os
import tempfile
from typing import Any

from fpdf import FPDF

from src.bot.database.models import Job, JobType


class JobPdfService:
    @staticmethod
    def _safe(value: str | None) -> str:
        if value is None:
            return "N/A"
        return str(value).encode("latin-1", errors="replace").decode("latin-1")

    @staticmethod
    def _job_type_text(job_type: JobType) -> str:
        return "Quote Job" if job_type == JobType.QUOTE else "Preset Price Job"

    @staticmethod
    def _fmt_dt(value: datetime | None) -> str:
        return value.strftime("%Y-%m-%d %H:%M") if value else "N/A"

    @staticmethod
    def _soft_wrap_long_tokens(text: str, token_len: int = 40) -> str:
        parts = []
        for token in text.split(" "):
            if len(token) <= token_len:
                parts.append(token)
                continue
            chunks = [token[i:i + token_len] for i in range(0, len(token), token_len)]
            parts.append("\n".join(chunks))
        return " ".join(parts)

    @staticmethod
    def _extract_photo_ids(raw_ids: str | None, max_count: int = 3) -> list[str]:
        if not raw_ids:
            return []
        return [photo_id.strip() for photo_id in raw_ids.split(",") if photo_id.strip()][:max_count]

    @staticmethod
    async def _download_temp_photo(bot: Any, file_id: str) -> str:
        tg_file = await bot.get_file(file_id)
        downloaded = await bot.download_file(tg_file.file_path)

        if hasattr(downloaded, "seek"):
            downloaded.seek(0)
        content = downloaded.read()

        suffix = os.path.splitext(tg_file.file_path or "")[1].lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            return temp_file.name

    @classmethod
    async def _add_photo_gallery(cls, pdf: FPDF, bot: Any | None, photo_ids: list[str], section_title: str):
        if not bot or not photo_ids:
            return

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, cls._safe(section_title), ln=True)

        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        added = 0

        for idx, photo_id in enumerate(photo_ids, start=1):
            temp_path = None
            try:
                temp_path = await cls._download_temp_photo(bot, photo_id)
                pdf.set_font("Helvetica", size=10)
                pdf.cell(0, 7, f"Photo {idx}", ln=True)
                pdf.image(temp_path, w=page_width)
                pdf.ln(2)
                added += 1
            except Exception:
                continue
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

        if added == 0:
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 7, "No photos could be embedded into this PDF.")
        pdf.ln(1)

    @classmethod
    def _base_pdf(cls, title: str) -> FPDF:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, cls._safe(title), ln=True)
        pdf.ln(3)
        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 8, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
        pdf.ln(2)
        return pdf

    @classmethod
    def _add_field(cls, pdf: FPDF, label: str, value: str | None):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, cls._safe(label), ln=True)
        pdf.set_font("Helvetica", size=11)
        safe_value = cls._soft_wrap_long_tokens(cls._safe(value))
        pdf.multi_cell(0, 8, safe_value)
        pdf.ln(1)

    @classmethod
    async def build_job_dispatch_pdf(
        cls,
        job: Job,
        supervisor_name: str | None = None,
        recipient_name: str | None = None,
        bot: Any | None = None,
    ) -> tuple[str, bytes]:
        pdf = cls._base_pdf(f"Work Order - Job #{job.id}")

        cls._add_field(pdf, "Job ID:", str(job.id))
        cls._add_field(pdf, "Title:", job.title)
        cls._add_field(pdf, "Type:", cls._job_type_text(job.job_type))
        cls._add_field(pdf, "Supervisor:", supervisor_name or "N/A")
        cls._add_field(pdf, "Assigned to:", recipient_name or "Open/Broadcast")
        cls._add_field(pdf, "Address:", job.address)
        cls._add_field(pdf, "Description:", job.description)
        cls._add_field(pdf, "Preset Price:", job.preset_price)
        cls._add_field(pdf, "Deadline:", cls._fmt_dt(job.deadline))
        cls._add_field(pdf, "Created At:", cls._fmt_dt(job.created_at))
        await cls._add_photo_gallery(
            pdf,
            bot,
            cls._extract_photo_ids(job.supervisor_photos),
            "Job Photos:",
        )

        out = pdf.output(dest="S")
        if isinstance(out, str):
            content = out.encode("latin-1")
        else:
            content = bytes(out)
        return f"job_{job.id}_work_order.pdf", content

    @classmethod
    async def build_job_completion_pdf(
        cls,
        job: Job,
        subcontractor_name: str | None = None,
        notes: str | None = None,
        photo_count: int = 0,
        bot: Any | None = None,
    ) -> tuple[str, bytes]:
        pdf = cls._base_pdf(f"Completion Report - Job #{job.id}")

        cls._add_field(pdf, "Job ID:", str(job.id))
        cls._add_field(pdf, "Title:", job.title)
        cls._add_field(pdf, "Type:", cls._job_type_text(job.job_type))
        cls._add_field(pdf, "Subcontractor:", subcontractor_name)
        cls._add_field(pdf, "Company:", job.company_name)
        cls._add_field(pdf, "Address:", job.address)
        cls._add_field(pdf, "Submitted Notes:", notes)
        cls._add_field(pdf, "Submitted Photos:", str(photo_count))
        cls._add_field(pdf, "Accepted At:", cls._fmt_dt(job.accepted_at))
        cls._add_field(pdf, "Submitted At:", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        await cls._add_photo_gallery(
            pdf,
            bot,
            cls._extract_photo_ids(job.photos),
            "Completion Photos:",
        )

        out = pdf.output(dest="S")
        if isinstance(out, str):
            content = out.encode("latin-1")
        else:
            content = bytes(out)
        return f"job_{job.id}_completion_report.pdf", content
