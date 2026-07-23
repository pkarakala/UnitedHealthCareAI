"""
Celery task that runs the PA workflow out of band.

Dispatched by the prescription-intake endpoint when settings.async_workflow is
True. The endpoint creates the PA row synchronously (so it can return the id)
and this task runs the intake agent plus any auto-advances.
"""
import structlog

from app.celery_app import celery
from app.tasks.worker_db import run_task

logger = structlog.get_logger()


@celery.task(
    name="app.tasks.workflow_tasks.run_pa_workflow",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def run_pa_workflow(self, prior_auth_id: str):
    """Run the intake agent and initial auto-advance for a freshly created PA."""
    from app.agents.orchestrator import Orchestrator
    from app.models.prior_auth import PriorAuth

    async def _run(db):
        pa = await db.get(PriorAuth, prior_auth_id)
        if not pa:
            logger.error("workflow_task.pa_not_found", prior_auth_id=prior_auth_id)
            return {"prior_auth_id": prior_auth_id, "status": "not_found"}

        orchestrator = Orchestrator(db)
        result = await orchestrator.run_intake(prior_auth_id)

        # Re-read to report the status the workflow left the PA in.
        await db.refresh(pa)
        return {"prior_auth_id": pa.id, "status": pa.status, "success": result.success}

    try:
        return run_task(_run)
    except Exception as exc:  # pragma: no cover - exercised via Celery retry
        logger.error("workflow_task.error", prior_auth_id=prior_auth_id, error=str(exc))
        raise self.retry(exc=exc)
