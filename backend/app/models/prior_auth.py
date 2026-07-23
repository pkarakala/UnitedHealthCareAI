from sqlalchemy import String, Boolean, Integer, Text, Numeric, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.models.base import Base, AuditMixin
from app.utils.constants import PAStatus


class PriorAuth(Base, AuditMixin):
    __tablename__ = "prior_auths"

    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False)
    prescription_id: Mapped[str] = mapped_column(
        ForeignKey("prescriptions.id"), nullable=False
    )
    insurance_id: Mapped[str | None] = mapped_column(
        ForeignKey("insurances.id"), nullable=True
    )

    # State Machine
    status: Mapped[str] = mapped_column(
        String(50), default=PAStatus.INTAKE.value, nullable=False, index=True
    )
    sub_status: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # External References
    pa_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    confirmation_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    submission_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expected_response_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Decision
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    denial_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    denial_codes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Clinical
    medical_necessity_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_documents: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    collected_documents: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Revenue
    claim_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    revenue_recovered: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Simulation tracking — True when any agent wrote simulated (LLM-invented)
    # external data to this PA. simulated_agents lists which agents did so.
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    simulated_agents: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Workflow
    current_agent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="prior_auths")
    prescription = relationship("Prescription", back_populates="prior_auths")
    communications = relationship("Communication", back_populates="prior_auth")
    documents = relationship("ClinicalDocument", back_populates="prior_auth")
    appeals = relationship("Appeal", back_populates="prior_auth")
    agent_executions = relationship("AgentExecution", back_populates="prior_auth")
