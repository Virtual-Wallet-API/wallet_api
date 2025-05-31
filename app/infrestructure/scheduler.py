from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.config import DB_URL


# Create a singleton scheduler instance
class SchedulerManager:
    _instance = None

    @classmethod
    def get_scheduler(cls):
        if cls._instance is None:
            # Configure the scheduler with SQLAlchemy job store for persistence
            jobstores = {
                'default': SQLAlchemyJobStore(url=DB_URL)
            }

            cls._instance = BackgroundScheduler(jobstores=jobstores)

        return cls._instance


# Function to initialize and start the scheduler
def init_scheduler() -> BackgroundScheduler:
    scheduler = SchedulerManager.get_scheduler()
    if not scheduler.running:
        scheduler.start()

    return scheduler


# Function to add a job to run daily at a specific time
def schedule_daily_job(func, hour, minute, job_id=None, **kwargs):
    """
    Schedule a function to run daily at the specified time

    Args:
        func: The function to execute
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
        job_id: Optional unique identifier for the job
        **kwargs: Additional arguments to pass to the function
    """
    scheduler = SchedulerManager.get_scheduler()

    # Create a cron trigger for daily execution at the specified time
    trigger = CronTrigger(hour=hour, minute=minute)

    # Add the job to the scheduler
    scheduler.add_job(
        func=func,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        kwargs=kwargs
    )

    return job_id