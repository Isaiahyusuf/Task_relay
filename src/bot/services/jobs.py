from datetime import datetime
from sqlalchemy import select, and_
from src.bot.database import async_session, Job, User
from src.bot.database.models import JobStatus, JobType
import logging

logger = logging.getLogger(__name__)

class JobService:
    @staticmethod
    async def create_job(
        supervisor_id: int,
        title: str,
        job_type: JobType,
        description: str | None = None,
        address: str | None = None,
        preset_price: str | None = None,
        photos: str | None = None,
        team_id: int | None = None
    ) -> Job | None:
        if not async_session:
            return None
        
        async with async_session() as session:
            job = Job(
                title=title,
                description=description,
                address=address,
                job_type=job_type,
                preset_price=preset_price,
                photos=photos,
                status=JobStatus.PENDING,
                supervisor_id=supervisor_id,
                team_id=team_id
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            return job
    
    @staticmethod
    async def dispatch_job(job_id: int, subcontractor_id: int) -> bool:
        if not async_session:
            return False
        
        async with async_session() as session:
            result = await session.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job or job.status != JobStatus.PENDING:
                return False
            
            job.subcontractor_id = subcontractor_id
            job.status = JobStatus.DISPATCHED
            job.dispatched_at = datetime.utcnow()
            
            await session.commit()
            return True
    
    @staticmethod
    async def accept_job(job_id: int, telegram_id: int, quoted_price: str | None = None) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not configured"
        
        async with async_session() as session:
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return False, "User not found"
            
            result = await session.execute(
                select(Job).where(
                    and_(Job.id == job_id, Job.subcontractor_id == user.id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found or not assigned to you"
            
            if job.status != JobStatus.DISPATCHED:
                return False, "This job is not available for acceptance"
            
            job.status = JobStatus.ACCEPTED
            job.responded_at = datetime.utcnow()
            
            if quoted_price and job.job_type == JobType.QUOTE:
                job.quoted_price = quoted_price
            
            await session.commit()
            return True, "Job accepted successfully!"
    
    @staticmethod
    async def decline_job(job_id: int, telegram_id: int, reason: str | None = None) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not configured"
        
        async with async_session() as session:
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return False, "User not found"
            
            result = await session.execute(
                select(Job).where(
                    and_(Job.id == job_id, Job.subcontractor_id == user.id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found or not assigned to you"
            
            if job.status != JobStatus.DISPATCHED:
                return False, "This job is not available for decline"
            
            job.status = JobStatus.DECLINED
            job.responded_at = datetime.utcnow()
            job.decline_reason = reason
            
            await session.commit()
            return True, "Job declined."
    
    @staticmethod
    async def get_pending_jobs_for_subcontractor(telegram_id: int) -> list[Job]:
        if not async_session:
            return []
        
        async with async_session() as session:
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return []
            
            result = await session.execute(
                select(Job).where(
                    and_(
                        Job.subcontractor_id == user.id,
                        Job.status == JobStatus.DISPATCHED
                    )
                ).order_by(Job.dispatched_at.desc())
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def get_job_history(team_id: int | None = None, limit: int = 50) -> list[Job]:
        if not async_session:
            return []
        
        async with async_session() as session:
            query = select(Job).where(Job.status != JobStatus.ARCHIVED)
            
            if team_id:
                query = query.where(Job.team_id == team_id)
            
            query = query.order_by(Job.created_at.desc()).limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
