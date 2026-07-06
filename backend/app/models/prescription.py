from sqlalchemy import String, Integer, Float, Text, Date, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin


class Prescription(Base, AuditMixin):
    __tablename__ = "prescriptions"

    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False)
    prescriber_npi: Mapped[str] = mapped_column(String(10), nullable=False)
    prescriber_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prescriber_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prescriber_fax: Mapped[str | None] = mapped_column(String(20), nullable=True)
    drug_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ndc: Mapped[str | None] = mapped_column(String(11), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    days_supply: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refills: Mapped[int | None] = mapped_column(Integer, nullable=True)
    directions: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    pharmacy_npi: Mapped[str | None] = mapped_column(String(10), nullable=True)
    date_written: Mapped[str | None] = mapped_column(Date, nullable=True)
    raw_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="intake")

    patient = relationship("Patient", back_populates="prescriptions")
    prior_auths = relationship("PriorAuth", back_populates="prescription")
