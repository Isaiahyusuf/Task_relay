from datetime import datetime, timedelta
from sqlalchemy import select, and_
from src.bot.database import async_session, Job
from src.bot.database.models import JobStatus
from src.bot.config import config
import logging

logger = logging.getLogger(__name__)

class ArchiveService:
    @staticmethod
    async def archive_old_jobs() -> int:
        if not async_session:
            return 0
        
        cutoff_date = datetime.utcnow() - timedelta(days=config.ARCHIVE_AFTER_DAYS)
        
        async with async_session() as session:
            result = await session.execute(
                select(Job).where(
                    and_(
                        Job.status.in_([JobStatus.ACCEPTED, JobStatus.DECLINED, JobStatus.COMPLETED]),
                        Job.created_at < cutoff_date,
                        Job.archived_at == None
                    )
                )
            )
            jobs = result.scalars().all()
            
            count = 0
            for job in jobs:
                job.status = JobStatus.ARCHIVED
                job.archived_at = datetime.utcnow()
                count += 1
            
            await session.commit()
            
            if count > 0:
                logger.info(f"Archived {count} jobs older than {config.ARCHIVE_AFTER_DAYS} days")
            
            return count
    
    @staticmethod
    async def get_archived_jobs(team_id: int | None = None, limit: int = 50) -> list[Job]:
        if not async_session:
            return []
        
        async with async_session() as session:
            query = select(Job).where(Job.status == JobStatus.ARCHIVED)
            
            if team_id:
                query = query.where(Job.team_id == team_id)
            
            query = query.order_by(Job.archived_at.desc()).limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
