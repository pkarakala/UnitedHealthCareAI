import uuid
from datetime import datetime, timezone

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_id: str = None,
        details: dict = None,
        phi_accessed: bool = False,
        ip_address: str = None,
    ):
        entry = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            phi_accessed=phi_accessed,
            ip_address=ip_address,
        )
        self.db.add(entry)
        await self.db.flush()


class AuditContext:
    """
    Request-scoped audit helper injected into PHI-touching endpoints.

    Captures the acting user and client IP once, so endpoints can record an
    access with a single `await audit.record(...)` call. The entry is flushed
    into the caller's session and persisted by the endpoint's own commit, so
    the audit row shares the request's transaction.
    """

    def __init__(self, db: AsyncSession, request: Request):
        self.db = db
        self.request = request
        # Resolved lazily so endpoints on unauthenticated routers still work.
        self.user_id: str | None = None

    def _client_ip(self) -> str | None:
        forwarded = self.request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.request.client.host if self.request.client else None

    async def record(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict | None = None,
        phi_accessed: bool = True,
    ) -> None:
        await AuditService(self.db).log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=self.user_id,
            details=details,
            phi_accessed=phi_accessed,
            ip_address=self._client_ip(),
        )


def get_audit_context(request: Request, db: AsyncSession = Depends(get_db)) -> AuditContext:
    """FastAPI dependency yielding a request-scoped AuditContext."""
    ctx = AuditContext(db, request)
    user = getattr(request.state, "user", None)
    if user is not None:
        ctx.user_id = user.id
    return ctx
