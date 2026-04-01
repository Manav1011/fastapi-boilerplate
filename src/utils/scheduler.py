from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

scheduler = AsyncIOScheduler(
    job_defaults={"coalesce": False, "max_instances": 1}, timezone=utc
)
