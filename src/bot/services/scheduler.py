import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from src.bot.database import async_session, Job, User
from src.bot.database.models import JobStatus
from src.bot.config import config
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    bot = None
    
    @classmethod
    def set_bot(cls, bot):
        cls.bot = bot
    
    @classmethod
    async def run_scheduler(cls):
        logger.info("Starting background scheduler")
        while True:
            try:
                await cls.check_reminders()
                await cls.check_auto_close()
                await asyncio.sleep(1800)
            except asyncio.CancelledError:
                logger.info("Scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    @classmethod
    async def check_reminders(cls):
        if not async_session or not cls.bot:
            return
        
        reminder_cutoff = datetime.utcnow() - timedelta(hours=config.RESPONSE_REMINDER_HOURS)
        
        async with async_session() as session:
            result = await session.execute(
                select(Job, User).join(
                    User, Job.subcontractor_id == User.id
                ).where(
                    and_(
                        Job.status == JobStatus.SENT,
                        Job.sent_at < reminder_cutoff,
                        Job.reminder_sent == False,
                        Job.subcontractor_id != None
                    )
                )
            )
            jobs_with_users = result.all()
            
            for job, user in jobs_with_users:
                try:
                    await cls.bot.send_message(
                        user.telegram_id,
                        f"*Reminder: Pending Job*\n\n"
                        f"You have a pending job that requires your response:\n\n"
                        f"*Job #{job.id}:* {job.title}\n\n"
                        f"Please accept or decline this job.",
                        parse_mode="Markdown"
                    )
                    
                    job.reminder_sent = True
                    job.reminder_sent_at = datetime.utcnow()
                    logger.info(f"Sent reminder for job {job.id} to user {user.telegram_id}")
                except Exception as e:
                    logger.error(f"Failed to send reminder for job {job.id}: {e}")
            
            await session.commit()
    
    @classmethod
    async def check_auto_close(cls):
        if not async_session or not cls.bot:
            return
        
        close_cutoff = datetime.utcnow() - timedelta(hours=config.JOB_AUTO_CLOSE_HOURS)
        
        async with async_session() as session:
            result = await session.execute(
                select(Job, User).join(
                    User, Job.supervisor_id == User.id
                ).where(
                    and_(
                        Job.status == JobStatus.SENT,
                        Job.sent_at < close_cutoff
                    )
                )
            )
            jobs_with_supervisors = result.all()
            
            for job, supervisor in jobs_with_supervisors:
                try:
                    job.status = JobStatus.CANCELLED
                    job.cancelled_at = datetime.utcnow()
                    
                    await cls.bot.send_message(
                        supervisor.telegram_id,
                        f"*Job Auto-Cancelled*\n\n"
                        f"Job #{job.id}: {job.title}\n\n"
                        f"This job was automatically cancelled due to no response "
                        f"after {config.JOB_AUTO_CLOSE_HOURS} hours.",
                        parse_mode="Markdown"
                    )
                    
                    logger.info(f"Auto-cancelled job {job.id}")
                except Exception as e:
                    logger.error(f"Failed to auto-close job {job.id}: {e}")
            
            await session.commit()
