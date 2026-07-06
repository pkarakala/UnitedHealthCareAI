import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

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
