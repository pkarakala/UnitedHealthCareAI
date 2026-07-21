"""
Demo seed: Populates the database with realistic PA data for demos/presentations.
Run via the API or Railway console.
"""
import asyncio
import uuid
import os
import sys
from datetime import date, datetime, timezone, timedelta

sys.path.insert(0, "/app")

from app.database import engine
from app.models.base import Base
from app.models.patient import Patient
from app.models.insurance import Insurance
from app.models.prescription import Prescription
from app.models.prior_auth import PriorAuth
from app.models.communication import Communication
from app.models.agent_execution import AgentExecution

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with AsyncSessionLocal() as db:
        # Insurance Plans
        bcbs = Insurance(
            id=str(uuid.uuid4()),
            plan_name="BlueCross BlueShield PPO",
            payer_name="BCBS",
            bin_number="003585",
            pcn="MEDDADV",
            group_number="GRP001",
            phone="1-800-555-0100",
            fax="1-800-555-0101",
            is_active=True,
            formulary_data={"ozempic": {"tier": 3, "pa_required": True}},
        )
        aetna = Insurance(
            id=str(uuid.uuid4()),
            plan_name="Aetna Commercial HMO",
            payer_name="Aetna",
            bin_number="004336",
            pcn="ADV",
            group_number="GRP002",
            phone="1-800-555-0200",
            is_active=True,
        )
        cigna = Insurance(
            id=str(uuid.uuid4()),
            plan_name="Cigna Open Access Plus",
            payer_name="Cigna",
            bin_number="003858",
            pcn="CIGNA01",
            group_number="GRP003",
            is_active=True,
        )
        db.add_all([bcbs, aetna, cigna])

        # Patients
        patients_data = [
            {"first_name": "James", "last_name": "Mitchell", "dob": date(1962, 4, 12), "phone": "5551234567", "email": "j.mitchell@email.com", "member_id": "MBR001234", "insurance": bcbs},
            {"first_name": "Maria", "last_name": "Rodriguez", "dob": date(1975, 8, 23), "phone": "5559876543", "email": "maria.r@email.com", "member_id": "MBR005678", "insurance": aetna},
            {"first_name": "Robert", "last_name": "Chen", "dob": date(1958, 11, 5), "phone": "5554567890", "email": "r.chen@email.com", "member_id": "MBR009012", "insurance": cigna},
            {"first_name": "Sarah", "last_name": "Williams", "dob": date(1983, 2, 17), "phone": "5557890123", "email": "s.williams@email.com", "member_id": "MBR003456", "insurance": bcbs},
            {"first_name": "David", "last_name": "Thompson", "dob": date(1970, 6, 30), "phone": "5552345678", "email": "d.thompson@email.com", "member_id": "MBR007890", "insurance": aetna},
            {"first_name": "Lisa", "last_name": "Garcia", "dob": date(1968, 9, 8), "phone": "5556789012", "email": "l.garcia@email.com", "member_id": "MBR004321", "insurance": cigna},
            {"first_name": "Michael", "last_name": "Johnson", "dob": date(1955, 12, 14), "phone": "5553456789", "email": "m.johnson@email.com", "member_id": "MBR008765", "insurance": bcbs},
            {"first_name": "Jennifer", "last_name": "Park", "dob": date(1979, 3, 25), "phone": "5558901234", "email": "j.park@email.com", "member_id": "MBR002109", "insurance": aetna},
        ]

        patients = []
        for p in patients_data:
            patient = Patient(
                id=str(uuid.uuid4()),
                first_name=p["first_name"],
                last_name=p["last_name"],
                date_of_birth=p["dob"],
                phone=p["phone"],
                email=p["email"],
                member_id=p["member_id"],
                insurance_id=p["insurance"].id,
            )
            patients.append(patient)
            db.add(patient)

        # Prescriptions + PAs
        rx_data = [
            {"patient": 0, "drug": "Ozempic", "ndc": "00169416112", "strength": "1mg/dose", "qty": 4, "days": 28, "dr": "Dr. Sarah Johnson", "npi": "1234567890", "status": "approved", "revenue": 1250.00},
            {"patient": 1, "drug": "Dupixent", "ndc": "00024593201", "strength": "300mg/2mL", "qty": 2, "days": 28, "dr": "Dr. Michael Chen", "npi": "9876543210", "status": "pending_review", "revenue": None},
            {"patient": 2, "drug": "Humira", "ndc": "00074309502", "strength": "40mg/0.8mL", "qty": 2, "days": 28, "dr": "Dr. Emily Davis", "npi": "5678901234", "status": "approved", "revenue": 6800.00},
            {"patient": 3, "drug": "Entresto", "ndc": "00078063520", "strength": "97/103mg", "qty": 60, "days": 30, "dr": "Dr. James Wilson", "npi": "3456789012", "status": "denied", "revenue": None},
            {"patient": 4, "drug": "Xeljanz", "ndc": "00069102130", "strength": "5mg", "qty": 60, "days": 30, "dr": "Dr. Lisa Park", "npi": "7890123456", "status": "appeal_in_progress", "revenue": None},
            {"patient": 5, "drug": "Repatha", "ndc": "55513073001", "strength": "140mg/mL", "qty": 1, "days": 28, "dr": "Dr. Robert Taylor", "npi": "2345678901", "status": "submitted", "revenue": None},
            {"patient": 6, "drug": "Mounjaro", "ndc": "00002140580", "strength": "5mg/0.5mL", "qty": 4, "days": 28, "dr": "Dr. Sarah Johnson", "npi": "1234567890", "status": "approved", "revenue": 1100.00},
            {"patient": 7, "drug": "Stelara", "ndc": "57894003001", "strength": "45mg/0.5mL", "qty": 1, "days": 84, "dr": "Dr. Michael Chen", "npi": "9876543210", "status": "clinical_review", "revenue": None},
            {"patient": 0, "drug": "Jardiance", "ndc": "00597015130", "strength": "25mg", "qty": 30, "days": 30, "dr": "Dr. Sarah Johnson", "npi": "1234567890", "status": "approved", "revenue": 580.00},
            {"patient": 1, "drug": "Trulicity", "ndc": "00002140701", "strength": "1.5mg/0.5mL", "qty": 4, "days": 28, "dr": "Dr. Emily Davis", "npi": "5678901234", "status": "doctor_outreach", "revenue": None},
            {"patient": 3, "drug": "Eliquis", "ndc": "00003089321", "strength": "5mg", "qty": 60, "days": 30, "dr": "Dr. James Wilson", "npi": "3456789012", "status": "approved", "revenue": 520.00},
            {"patient": 5, "drug": "Keytruda", "ndc": "00006334902", "strength": "200mg/8mL", "qty": 1, "days": 21, "dr": "Dr. Robert Taylor", "npi": "2345678901", "status": "form_filling", "revenue": None},
        ]

        now = datetime.now(timezone.utc)
        for i, rx in enumerate(rx_data):
            rx_id = str(uuid.uuid4())
            pa_id = str(uuid.uuid4())
            created = now - timedelta(days=12 - i, hours=i * 3)

            prescription = Prescription(
                id=rx_id,
                patient_id=patients[rx["patient"]].id,
                prescriber_npi=rx["npi"],
                prescriber_name=rx["dr"],
                drug_name=rx["drug"],
                ndc=rx["ndc"],
                strength=rx["strength"],
                quantity=rx["qty"],
                days_supply=rx["days"],
                directions="As directed by physician",
                source="electronic",
                status="verified",
                created_at=created,
            )
            db.add(prescription)

            pa = PriorAuth(
                id=pa_id,
                patient_id=patients[rx["patient"]].id,
                prescription_id=rx_id,
                insurance_id=patients[rx["patient"]].insurance_id,
                status=rx["status"],
                current_agent="status_monitoring" if rx["status"] == "pending_review" else None,
                priority=3 if rx["status"] == "denied" else 5,
                claim_amount=float(rx["qty"]) * 150.0,
                revenue_recovered=rx["revenue"],
                decision="approved" if rx["status"] == "approved" else ("denied" if rx["status"] == "denied" else None),
                submitted_at=created + timedelta(hours=4) if rx["status"] not in ("clinical_review", "doctor_outreach", "form_filling") else None,
                decision_at=created + timedelta(hours=48) if rx["status"] in ("approved", "denied") else None,
                created_at=created,
            )
            db.add(pa)

            # Add agent executions for completed PAs
            if rx["status"] in ("approved", "denied", "pending_review", "submitted"):
                agents_run = ["prescription_intake", "pa_detection", "insurance_verification", "clinical_requirement", "pa_form_filling", "clinical_writing", "submission"]
                for j, agent_name in enumerate(agents_run):
                    execution = AgentExecution(
                        id=str(uuid.uuid4()),
                        prior_auth_id=pa_id,
                        agent_name=agent_name,
                        status="completed",
                        started_at=created + timedelta(minutes=j * 2),
                        completed_at=created + timedelta(minutes=j * 2 + 1),
                        duration_ms=800 + (j * 200),
                        tokens_input=150 + (j * 50),
                        tokens_output=80 + (j * 30),
                        model_used="claude-sonnet-4-20250514",
                    )
                    db.add(execution)

        # Communications
        comms = [
            Communication(id=str(uuid.uuid4()), prior_auth_id=pa_id, channel="fax", direction="outbound", recipient="Dr. Sarah Johnson", subject="PA Documentation Request - Ozempic", body="Please provide clinical documentation...", status="delivered", sent_at=now - timedelta(days=5), created_at=now - timedelta(days=5)),
            Communication(id=str(uuid.uuid4()), prior_auth_id=pa_id, channel="email", direction="outbound", recipient="j.mitchell@email.com", subject="PA Update - Your medication was approved", body="Great news! Your prior authorization...", status="delivered", sent_at=now - timedelta(days=2), created_at=now - timedelta(days=2)),
            Communication(id=str(uuid.uuid4()), prior_auth_id=pa_id, channel="sms", direction="outbound", recipient="5551234567", subject="PA Status", body="Your Rx is ready for pickup.", status="sent", sent_at=now - timedelta(days=1), created_at=now - timedelta(days=1)),
        ]
        db.add_all(comms)

        await db.commit()
        print("Demo data seeded successfully!")
        print(f"  - 3 insurance plans")
        print(f"  - 8 patients")
        print(f"  - 12 prescriptions + PA cases")
        print(f"  - Agent execution logs")
        print(f"  - 3 communications")


if __name__ == "__main__":
    asyncio.run(seed())
