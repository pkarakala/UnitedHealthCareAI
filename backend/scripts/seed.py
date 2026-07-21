"""
Seed script: Populates the database with sample data for development/testing.
Run with: python scripts/seed.py (from within the container)
"""
import asyncio
import uuid
from datetime import date

import sys
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.patient import Patient
from app.models.insurance import Insurance
from app.models.prescription import Prescription


async def seed():
    async with AsyncSessionLocal() as db:
        # Create sample insurance plans
        insurance_plans = [
            Insurance(
                id=str(uuid.uuid4()),
                plan_name="BlueCross BlueShield PPO",
                payer_name="BCBS",
                bin_number="003585",
                pcn="MEDDADV",
                group_number="GRP001",
                phone="1-800-555-0100",
                fax="1-800-555-0101",
                portal_url=None,
                is_active=True,
                formulary_data={
                    "ozempic": {"tier": 3, "pa_required": True, "step_therapy": True},
                    "metformin": {"tier": 1, "pa_required": False},
                    "humira": {"tier": 4, "pa_required": True, "specialty": True},
                },
                pa_requirements={
                    "ozempic": {
                        "diagnoses": ["E11.x - Type 2 Diabetes"],
                        "labs": ["HbA1c > 7%"],
                        "prior_therapies": ["metformin 3+ months"],
                    }
                },
                step_therapy_rules={
                    "ozempic": ["metformin", "glipizide"],
                    "humira": ["methotrexate", "sulfasalazine"],
                },
            ),
            Insurance(
                id=str(uuid.uuid4()),
                plan_name="Aetna Commercial",
                payer_name="Aetna",
                bin_number="004336",
                pcn="ADV",
                group_number="GRP002",
                phone="1-800-555-0200",
                is_active=True,
                formulary_data={
                    "dupixent": {"tier": 4, "pa_required": True, "specialty": True},
                    "entresto": {"tier": 3, "pa_required": True},
                },
            ),
        ]

        for plan in insurance_plans:
            db.add(plan)

        # Create sample patients
        patients = [
            Patient(
                id=str(uuid.uuid4()),
                first_name="John",
                last_name="Smith",
                date_of_birth=date(1965, 3, 15),
                phone="5551234567",
                email="john.smith@email.com",
                member_id="MBR001234",
                group_number="GRP001",
                insurance_id=insurance_plans[0].id,
                address={"street": "123 Main St", "city": "Springfield", "state": "IL", "zip": "62701"},
            ),
            Patient(
                id=str(uuid.uuid4()),
                first_name="Maria",
                last_name="Garcia",
                date_of_birth=date(1978, 7, 22),
                phone="5559876543",
                email="maria.garcia@email.com",
                member_id="MBR005678",
                group_number="GRP002",
                insurance_id=insurance_plans[1].id,
                address={"street": "456 Oak Ave", "city": "Chicago", "state": "IL", "zip": "60601"},
            ),
        ]

        for patient in patients:
            db.add(patient)

        # Create sample prescriptions
        prescriptions = [
            Prescription(
                id=str(uuid.uuid4()),
                patient_id=patients[0].id,
                prescriber_npi="1234567890",
                prescriber_name="Dr. Sarah Johnson",
                prescriber_phone="5555551111",
                prescriber_fax="5555551112",
                drug_name="Ozempic",
                ndc="00169416112",
                strength="1mg/dose",
                quantity=4,
                days_supply=28,
                refills=5,
                directions="Inject 1mg subcutaneously once weekly",
                diagnosis_codes=["E11.65"],
                source="electronic",
                status="intake",
            ),
            Prescription(
                id=str(uuid.uuid4()),
                patient_id=patients[1].id,
                prescriber_npi="9876543210",
                prescriber_name="Dr. Michael Chen",
                prescriber_phone="5555552222",
                prescriber_fax="5555552223",
                drug_name="Dupixent",
                ndc="00024593201",
                strength="300mg/2mL",
                quantity=2,
                days_supply=28,
                refills=11,
                directions="Inject 300mg subcutaneously every 2 weeks",
                diagnosis_codes=["L20.9"],
                source="electronic",
                status="intake",
            ),
        ]

        for rx in prescriptions:
            db.add(rx)

        await db.commit()
        print(f"Seeded: {len(insurance_plans)} insurance plans")
        print(f"Seeded: {len(patients)} patients")
        print(f"Seeded: {len(prescriptions)} prescriptions")
        print("Done!")


if __name__ == "__main__":
    asyncio.run(seed())
