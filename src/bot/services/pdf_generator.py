from datetime import datetime

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
        pdf.cell(50, 8, cls._safe(label), border=0)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 8, cls._safe(value))

    @classmethod
    def build_job_dispatch_pdf(
        cls,
        job: Job,
        supervisor_name: str | None = None,
        recipient_name: str | None = None,
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

        out = pdf.output(dest="S")
        if isinstance(out, str):
            content = out.encode("latin-1")
        else:
            content = bytes(out)
        return f"job_{job.id}_work_order.pdf", content

    @classmethod
    def build_job_completion_pdf(
        cls,
        job: Job,
        subcontractor_name: str | None = None,
        notes: str | None = None,
        photo_count: int = 0,
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

        out = pdf.output(dest="S")
        if isinstance(out, str):
            content = out.encode("latin-1")
        else:
            content = bytes(out)
        return f"job_{job.id}_completion_report.pdf", content
