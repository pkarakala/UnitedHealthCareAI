from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin


class Insurance(Base, AuditMixin):
    __tablename__ = "insurances"

    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bin_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    pcn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    group_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fax: Mapped[str | None] = mapped_column(String(20), nullable=True)
    portal_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    formulary_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pa_requirements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    step_therapy_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quantity_limits: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    patients = relationship("Patient", back_populates="insurance")
