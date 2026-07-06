from sqlalchemy import String, Date, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin


class Patient(Base, AuditMixin):
    __tablename__ = "patients"

    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(Date, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    member_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    group_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    insurance_id: Mapped[str | None] = mapped_column(
        ForeignKey("insurances.id"), nullable=True
    )

    insurance = relationship("Insurance", back_populates="patients")
    prescriptions = relationship("Prescription", back_populates="patient")
    prior_auths = relationship("PriorAuth", back_populates="patient")
