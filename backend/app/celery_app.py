from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery = Celery(
    "prior_auth",
    broker=settings.redis_url,
    backend=settings.redis_url,
    # Import task modules on worker startup so their @celery.task decorators
    # register. (autodiscover_tasks looks for a `tasks` submodule per package,
    # which these module names are not, so it wouldn't find them.)
    include=[
        "app.tasks.workflow_tasks",
        "app.tasks.monitoring_tasks",
        "app.tasks.followup_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.notification_tasks",
    ],
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
        # minute="*/120" was invalid (minutes are 0-59) and silently ran hourly.
        "schedule": crontab(minute=0, hour="*/2"),  # every 2 hours
    },
    "process-followups": {
        "task": "app.tasks.followup_tasks.process_scheduled_followups",
        "schedule": crontab(minute=0),  # every hour, on the hour
    },
    "nightly-analytics-rollup": {
        "task": "app.tasks.analytics_tasks.compute_daily_metrics",
        "schedule": crontab(hour=2, minute=0),  # 2 AM UTC
    },
}

