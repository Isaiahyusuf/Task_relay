from datetime import datetime
from sqlalchemy import select, or_
from src.bot.database import async_session, Job, User
from src.bot.database.models import JobType, JobStatus, UserRole, AvailabilityStatus
import logging

logger = logging.getLogger(__name__)

class JobService:
    @staticmethod
    async def create_job(
        supervisor_id: int,
        title: str,
        job_type: JobType,
        description: str = None,
        address: str = None,
        preset_price: str = None,
        team_id: int = None
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
                supervisor_id=supervisor_id,
                team_id=team_id,
                status=JobStatus.CREATED,
                created_at=datetime.utcnow()
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            return job
    
    @staticmethod
    async def send_job(job_id: int, subcontractor_id: int = None) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not available"
        
        async with async_session() as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found"
            
            if job.status == JobStatus.ARCHIVED:
                return False, "Cannot modify archived job"
            
            if job.status != JobStatus.CREATED:
                return False, f"Job must be in CREATED status to send (current: {job.status.value})"
            
            if subcontractor_id:
                sub_result = await session.execute(
                    select(User).where(User.id == subcontractor_id)
                )
                subcontractor = sub_result.scalar_one_or_none()
                
                if not subcontractor:
                    return False, "Subcontractor not found"
                
                if subcontractor.availability_status != AvailabilityStatus.AVAILABLE:
                    return False, "Subcontractor is not available"
                
                job.subcontractor_id = subcontractor_id
            
            job.status = JobStatus.SENT
            job.sent_at = datetime.utcnow()
            
            await session.commit()
            return True, "Job sent successfully"
    
    @staticmethod
    async def accept_job(job_id: int, telegram_id: int) -> tuple[bool, str, int | None]:
        if not async_session:
            return False, "Database not available", None
        
        async with async_session() as session:
            job_result = await session.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found", None
            
            if job.status == JobStatus.ARCHIVED:
                return False, "Cannot modify archived job", None
            
            if job.status not in [JobStatus.SENT, JobStatus.CREATED]:
                return False, f"Job cannot be accepted (current status: {job.status.value})", None
            
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return False, "User not found", None
            
            job.status = JobStatus.ACCEPTED
            job.subcontractor_id = user.id
            job.accepted_at = datetime.utcnow()
            
            # Get supervisor's telegram_id for notification
            sup_result = await session.execute(
                select(User.telegram_id).where(User.id == job.supervisor_id)
            )
            supervisor_tg_id = sup_result.scalar()
            
            await session.commit()
            return True, "Job accepted successfully", supervisor_tg_id
    
    @staticmethod
    async def start_job(job_id: int, telegram_id: int) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not available"
        
        async with async_session() as session:
            job_result = await session.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found"
            
            if job.status == JobStatus.ARCHIVED:
                return False, "Cannot modify archived job"
            
            if job.status != JobStatus.ACCEPTED:
                return False, f"Job must be accepted before starting (current status: {job.status.value})"
            
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user or job.subcontractor_id != user.id:
                return False, "You are not assigned to this job"
            
            job.status = JobStatus.IN_PROGRESS
            job.started_at = datetime.utcnow()
            
            await session.commit()
            return True, "Job started"
    
    @staticmethod
    async def complete_job(job_id: int, telegram_id: int, is_supervisor: bool = False) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not available"
        
        async with async_session() as session:
            job_result = await session.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found"
            
            if job.status == JobStatus.ARCHIVED:
                return False, "Cannot modify archived job"
            
            if job.status == JobStatus.COMPLETED:
                return False, "Job is already completed"
            
            if job.status == JobStatus.CANCELLED:
                return False, "Cannot complete a cancelled job"
            
            if job.status not in [JobStatus.IN_PROGRESS, JobStatus.ACCEPTED]:
                return False, f"Job cannot be completed (current status: {job.status.value})"
            
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            if is_supervisor:
                if job.supervisor_id != user.id:
                    return False, "You don't have permission to complete this job"
            else:
                if job.subcontractor_id != user.id:
                    return False, "You are not assigned to this job"
            
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
            await session.commit()
            return True, "Job marked as complete"
    
    @staticmethod
    async def cancel_job(job_id: int, telegram_id: int) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not available"
        
        async with async_session() as session:
            job_result = await session.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found"
            
            if job.status == JobStatus.ARCHIVED:
                return False, "Cannot modify archived job"
            
            if job.status in [JobStatus.COMPLETED, JobStatus.CANCELLED]:
                return False, f"Job cannot be cancelled (current status: {job.status.value})"
            
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user or job.supervisor_id != user.id:
                return False, "You don't have permission to cancel this job"
            
            job.status = JobStatus.CANCELLED
            job.cancelled_at = datetime.utcnow()
            
            await session.commit()
            return True, "Job cancelled"
    
    @staticmethod
    async def decline_job(job_id: int, telegram_id: int, reason: str = None) -> tuple[bool, str]:
        if not async_session:
            return False, "Database not available"
        
        async with async_session() as session:
            job_result = await session.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return False, "Job not found"
            
            if job.status == JobStatus.ARCHIVED:
                return False, "Cannot modify archived job"
            
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            job.decline_reason = reason
            job.status = JobStatus.SENT
            job.subcontractor_id = None
            
            await session.commit()
            return True, "Job declined"
    
    @staticmethod
    async def get_supervisor_jobs(telegram_id: int, status_filter: list[JobStatus] = None) -> list:
        if not async_session:
            return []
        
        async with async_session() as session:
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return []
            
            query = select(Job).where(
                Job.supervisor_id == user.id,
                Job.status != JobStatus.ARCHIVED
            )
            
            if status_filter:
                query = query.where(Job.status.in_(status_filter))
            
            query = query.order_by(Job.created_at.desc())
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def get_pending_jobs_for_subcontractor(telegram_id: int) -> list:
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
                    or_(
                        Job.subcontractor_id == user.id,
                        Job.subcontractor_id == None
                    ),
                    Job.status == JobStatus.SENT
                ).order_by(Job.created_at.desc())
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def get_subcontractor_active_jobs(telegram_id: int) -> list:
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
                    Job.subcontractor_id == user.id,
                    Job.status.in_([JobStatus.ACCEPTED, JobStatus.IN_PROGRESS])
                ).order_by(Job.created_at.desc())
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def get_job_history(team_id: int = None, limit: int = 50) -> list:
        if not async_session:
            return []
        
        async with async_session() as session:
            query = select(Job).where(Job.status != JobStatus.ARCHIVED)
            
            if team_id:
                query = query.where(Job.team_id == team_id)
            
            query = query.order_by(Job.created_at.desc()).limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def get_available_subcontractors(team_id: int = None) -> list:
        if not async_session:
            return []
        
        async with async_session() as session:
            result = await session.execute(
                select(User).where(
                    User.role == UserRole.SUBCONTRACTOR,
                    User.is_active == True,
                    User.availability_status == AvailabilityStatus.AVAILABLE
                )
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def get_job_by_id(job_id: int) -> Job | None:
        if not async_session:
            return None
        
        async with async_session() as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            return result.scalar_one_or_none()
