import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from src.bot.database import async_session, Job, User, WeeklyAvailability
from src.bot.database.models import JobStatus, UserRole
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
                await cls.check_deadline_reminders()
                await cls.check_weekly_availability_survey()
                await cls.check_availability_reminder()
                await asyncio.sleep(1800)  # Run every 30 minutes
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
    
    @classmethod
    async def check_deadline_reminders(cls):
        """Send reminders for jobs approaching their deadline (within 24 hours)"""
        if not async_session or not cls.bot:
            return
        
        reminder_window = datetime.utcnow() + timedelta(hours=24)
        
        async with async_session() as session:
            # Find jobs with deadlines within the next 24 hours that haven't had a reminder
            result = await session.execute(
                select(Job, User).join(
                    User, Job.subcontractor_id == User.id
                ).where(
                    and_(
                        Job.status.in_([JobStatus.ACCEPTED, JobStatus.IN_PROGRESS]),
                        Job.deadline != None,
                        Job.deadline <= reminder_window,
                        Job.deadline > datetime.utcnow(),
                        Job.deadline_reminder_sent == False
                    )
                )
            )
            jobs_with_users = result.all()
            
            for job, user in jobs_with_users:
                try:
                    deadline_str = job.deadline.strftime("%d/%m/%Y") if job.deadline else "Unknown"
                    await cls.bot.send_message(
                        user.telegram_id,
                        f" *Deadline Reminder*\n\n"
                        f"Job #{job.id}: {job.title}\n"
                        f"Deadline: *{deadline_str}*\n\n"
                        f"This job is due soon. Please complete it on time.",
                        parse_mode="Markdown"
                    )
                    
                    job.deadline_reminder_sent = True
                    logger.info(f"Sent deadline reminder for job {job.id} to user {user.telegram_id}")
                except Exception as e:
                    logger.error(f"Failed to send deadline reminder for job {job.id}: {e}")
            
            await session.commit()
    
    @classmethod
    async def check_weekly_availability_survey(cls):
        # Weekly availability requests are manager-driven via "Request Availability".
        return
    
    @classmethod
    async def reset_weekly_availability(cls):
        """Reset weekly availability on Saturdays - records are archived, not deleted"""
        if not async_session or not cls.bot:
            return
        
        today = datetime.utcnow().date()
        
        # Only run on Saturdays (weekday 5)
        if today.weekday() != 5:
            return
        
        logger.info("Weekly availability reset triggered (Saturday)")
    
    @classmethod
    async def check_availability_reminder(cls):
        # Reminders are intentionally disabled because availability is requested manually by managers.
        return
    
    @classmethod
    async def notify_admins_of_availability(cls, week_start: datetime):
        """Notify managers of subcontractor availability for the week"""
        if not async_session or not cls.bot:
            return
        
        async with async_session() as session:
            # Get all availability responses for this week
            result = await session.execute(
                select(WeeklyAvailability, User).join(
                    User, WeeklyAvailability.subcontractor_id == User.id
                ).where(WeeklyAvailability.week_start == week_start)
            )
            responses = result.all()
            
            days_data = {
                "mon": {"available": [], "unavailable": []},
                "tue": {"available": [], "unavailable": []},
                "wed": {"available": [], "unavailable": []},
                "thu": {"available": [], "unavailable": []},
                "fri": {"available": [], "unavailable": []}
            }
            no_response = []
            
            for avail, user in responses:
                name = user.first_name or user.username or f"User {user.telegram_id}"
                if avail.responded_at is None:
                    no_response.append(name)
                    continue
                
                if avail.monday_available:
                    days_data["mon"]["available"].append(name)
                else:
                    days_data["mon"]["unavailable"].append(name)
                if avail.tuesday_available:
                    days_data["tue"]["available"].append(name)
                else:
                    days_data["tue"]["unavailable"].append(name)
                if avail.wednesday_available:
                    days_data["wed"]["available"].append(name)
                else:
                    days_data["wed"]["unavailable"].append(name)
                if avail.thursday_available:
                    days_data["thu"]["available"].append(name)
                else:
                    days_data["thu"]["unavailable"].append(name)
                if avail.friday_available:
                    days_data["fri"]["available"].append(name)
                else:
                    days_data["fri"]["unavailable"].append(name)
            
            day_names = [
                ("mon", "Monday", 0),
                ("tue", "Tuesday", 1),
                ("wed", "Wednesday", 2),
                ("thu", "Thursday", 3),
                ("fri", "Friday", 4)
            ]
            
            message = f" *Weekly Availability Report*\nWeek of {week_start.strftime('%d/%m/%Y')}\n\n"
            
            for day_code, day_name, offset in day_names:
                day_date = (week_start + timedelta(days=offset)).strftime("%d/%m")
                available = days_data[day_code]["available"]
                message += f"*{day_name} {day_date}:*\n"
                message += f" {', '.join(available) if available else 'None'}\n\n"
            
            if no_response:
                message += f" *No Response:* {', '.join(no_response)}"
            
            # Get managers only
            manager_result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            managers = manager_result.scalars().all()
            
            for manager in managers:
                try:
                    await cls.bot.send_message(
                        manager.telegram_id,
                        message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify manager {manager.telegram_id} of availability: {e}")

