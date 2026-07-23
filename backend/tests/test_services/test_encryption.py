import pytest

from app.utils.encryption import encrypt_phi, decrypt_phi


def test_encrypt_decrypt_round_trip():
    plaintext = "555-123-4567"
    ciphertext = encrypt_phi(plaintext)
    assert ciphertext != plaintext
    assert decrypt_phi(ciphertext) == plaintext


def test_empty_values_pass_through():
    assert encrypt_phi("") == ""
    assert encrypt_phi(None) is None
    assert decrypt_phi("") == ""
    assert decrypt_phi(None) is None


def test_decrypt_legacy_plaintext_returns_unchanged():
    # Rows written before encryption was enabled aren't valid Fernet tokens;
    # decrypt should return them as-is rather than raising.
    assert decrypt_phi("plain-legacy-value") == "plain-legacy-value"


def test_ciphertext_is_not_deterministic_but_decrypts():
    # Fernet embeds a random IV, so two encryptions differ but both decrypt.
    a = encrypt_phi("john.smith@example.com")
    b = encrypt_phi("john.smith@example.com")
    assert a != b
    assert decrypt_phi(a) == decrypt_phi(b) == "john.smith@example.com"


@pytest.mark.asyncio
async def test_encrypted_column_round_trips_through_orm(db_session):
    import uuid
    from datetime import date
    from sqlalchemy import select
    from app.models.patient import Patient

    patient = Patient(
        id=str(uuid.uuid4()),
        first_name="Round",
        last_name="Trip",
        date_of_birth=date(1990, 1, 1),
        phone="5551234567",
        email="round.trip@example.com",
    )
    db_session.add(patient)
    await db_session.commit()
    db_session.expunge_all()

    fetched = (
        await db_session.execute(select(Patient).where(Patient.id == patient.id))
    ).scalar_one()
    assert fetched.phone == "5551234567"
    assert fetched.email == "round.trip@example.com"
