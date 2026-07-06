from sqlalchemy import String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.models.base import Base, AuditMixin


class Appeal(Base, AuditMixin):
    __tablename__ = "appeals"

    prior_auth_id: Mapped[str] = mapped_column(
        ForeignKey("prior_auths.id"), nullable=False
    )
    appeal_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    denial_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    denial_codes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    appeal_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    appeal_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    clinical_references: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    prior_auth = relationship("PriorAuth", back_populates="appeals")
