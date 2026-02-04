from datetime import datetime
from sqlalchemy import select
from src.bot.database import async_session, Quote, Job, User
from src.bot.database.models import JobStatus, JobType
import logging

logger = logging.getLogger(__name__)

class QuoteService:
    @staticmethod
    async def submit_quote(job_id: int, telegram_id: int, amount: str, notes: str = None) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not available"
        
        async with async_session() as session:
            job_result = await session.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found"
            
            if job.status == JobStatus.ARCHIVED:
                return False, "Cannot quote on archived job"
            
            if job.job_type != JobType.QUOTE:
                return False, "This job does not accept quotes"
            
            if job.status not in [JobStatus.SENT]:
                return False, "Job is no longer accepting quotes"
            
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            if not user.is_active:
                return False, "Your account is not active"
            
            existing_quote = await session.execute(
                select(Quote).where(
                    Quote.job_id == job_id,
                    Quote.subcontractor_id == user.id,
                    Quote.is_declined == False
                )
            )
            active_quote = existing_quote.scalar_one_or_none()
            if active_quote:
                if active_quote.is_accepted:
                    return False, "Your quote was already accepted for this job"
                return False, "You have already submitted a quote for this job"
            
            quote = Quote(
                job_id=job_id,
                subcontractor_id=user.id,
                amount=amount,
                notes=notes,
                submitted_at=datetime.utcnow()
            )
            session.add(quote)
            await session.commit()
            
            return True, f"Quote of {amount} submitted successfully"
    
    @staticmethod
    async def get_quotes_for_job(job_id: int) -> list:
        if not async_session:
            return []
        
        async with async_session() as session:
            result = await session.execute(
                select(Quote, User).join(User, Quote.subcontractor_id == User.id).where(
                    Quote.job_id == job_id
                ).order_by(Quote.submitted_at)
            )
            return list(result.all())
    
    @staticmethod
    async def accept_quote(quote_id: int, supervisor_telegram_id: int) -> tuple[bool, str, int]:
        if not async_session:
            return False, "Database not available", 0
        
        async with async_session() as session:
            quote_result = await session.execute(
                select(Quote).where(Quote.id == quote_id)
            )
            quote = quote_result.scalar_one_or_none()
            
            if not quote:
                return False, "Quote not found", 0
            
            job_result = await session.execute(select(Job).where(Job.id == quote.job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found", 0
            
            if job.status == JobStatus.ARCHIVED:
                return False, "Cannot modify archived job", 0
            
            if job.status not in [JobStatus.SENT]:
                return False, f"Job is not accepting quotes (status: {job.status.value})", 0
            
            sup_result = await session.execute(
                select(User).where(User.telegram_id == supervisor_telegram_id)
            )
            supervisor = sup_result.scalar_one_or_none()
            
            if not supervisor or job.supervisor_id != supervisor.id:
                return False, "You don't have permission to accept quotes for this job", 0
            
            quote.is_accepted = True
            job.status = JobStatus.ACCEPTED
            job.subcontractor_id = quote.subcontractor_id
            job.accepted_quote_id = quote.id
            job.accepted_at = datetime.utcnow()
            
            await session.commit()
            
            return True, f"Quote accepted! Job assigned to subcontractor.", quote.subcontractor_id
    
    @staticmethod
    async def get_other_quote_subcontractors(job_id: int, accepted_subcontractor_id: int) -> list[int]:
        if not async_session:
            return []
        
        async with async_session() as session:
            result = await session.execute(
                select(Quote, User).join(User, Quote.subcontractor_id == User.id).where(
                    Quote.job_id == job_id,
                    Quote.subcontractor_id != accepted_subcontractor_id
                )
            )
            return [user.telegram_id for quote, user in result.all()]
    
    @staticmethod
    async def decline_quote(quote_id: int, supervisor_telegram_id: int, reason: str) -> tuple[bool, str, int, int, str]:
        """
        Decline a quote and return job to available status.
        Returns: (success, message, subcontractor_telegram_id, job_id, job_title)
        """
        if not async_session:
            return False, "Database not available", 0, 0, ""
        
        async with async_session() as session:
            quote_result = await session.execute(
                select(Quote).where(Quote.id == quote_id)
            )
            quote = quote_result.scalar_one_or_none()
            
            if not quote:
                return False, "Quote not found", 0, 0, ""
            
            job_result = await session.execute(select(Job).where(Job.id == quote.job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found", 0, 0, ""
            
            sup_result = await session.execute(
                select(User).where(User.telegram_id == supervisor_telegram_id)
            )
            supervisor = sup_result.scalar_one_or_none()
            
            if not supervisor or job.supervisor_id != supervisor.id:
                return False, "You don't have permission to decline quotes for this job", 0, 0, ""
            
            # Get subcontractor telegram_id
            sub_result = await session.execute(
                select(User).where(User.id == quote.subcontractor_id)
            )
            subcontractor = sub_result.scalar_one_or_none()
            sub_telegram_id = subcontractor.telegram_id if subcontractor else 0
            
            # Mark quote as declined
            quote.is_declined = True
            quote.decline_reason = reason
            
            await session.commit()
            
            return True, "Quote declined", sub_telegram_id, job.id, job.title
    
    @staticmethod
    async def can_resubmit_quote(job_id: int, telegram_id: int) -> tuple[bool, str]:
        """Check if a subcontractor can resubmit a quote (only if previous was declined)."""
        if not async_session:
            return False, "Database not available"
        
        async with async_session() as session:
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            existing_quote = await session.execute(
                select(Quote).where(
                    Quote.job_id == job_id,
                    Quote.subcontractor_id == user.id
                ).order_by(Quote.submitted_at.desc())
            )
            quote = existing_quote.scalar_one_or_none()
            
            if not quote:
                return True, "No previous quote"
            
            if quote.is_declined:
                return True, "Previous quote was declined, can resubmit"
            
            if quote.is_accepted:
                return False, "Your quote was already accepted"
            
            return False, "You have already submitted a quote for this job"
