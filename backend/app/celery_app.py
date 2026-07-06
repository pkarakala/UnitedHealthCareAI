from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery = Celery(
    "prior_auth",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery.conf.beat_schedule = {
    "monitor-pending-pas": {
        "task": "app.tasks.monitoring_tasks.check_pending_authorizations",
        "schedule": crontab(minute="*/120"),  # every 2 hours
    },
    "process-followups": {
        "task": "app.tasks.followup_tasks.process_scheduled_followups",
        "schedule": crontab(minute="*/60"),  # every hour
    },
    "nightly-analytics-rollup": {
        "task": "app.tasks.analytics_tasks.compute_daily_metrics",
        "schedule": crontab(hour=2, minute=0),  # 2 AM UTC
    },
}

celery.autodiscover_tasks(["app.tasks"])
