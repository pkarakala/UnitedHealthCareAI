import re


def validate_npi(npi: str) -> bool:
    """Validate a National Provider Identifier (10 digits, Luhn check)."""
    if not npi or not re.match(r"^\d{10}$", npi):
        return False
    # Luhn algorithm for NPI
    digits = [int(d) for d in npi]
    total = 24  # constant for health applications
    for i, d in enumerate(reversed(digits[:-1])):
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    check = (10 - (total % 10)) % 10
    return check == digits[-1]


def validate_ndc(ndc: str) -> bool:
    """Validate a National Drug Code (11 digits in 5-4-2 format)."""
    if not ndc:
        return False
    clean = ndc.replace("-", "")
    return bool(re.match(r"^\d{11}$", clean))


def validate_icd10(code: str) -> bool:
    """Validate an ICD-10-CM code format."""
    if not code:
        return False
    return bool(re.match(r"^[A-Z]\d{2}(\.\d{1,4})?$", code.upper()))


def validate_bin(bin_number: str) -> bool:
    """Validate a BIN (Bank Identification Number) - 6 digits."""
    if not bin_number:
        return False
    return bool(re.match(r"^\d{6}$", bin_number))


def format_phone(phone: str) -> str:
    """Format a phone number to (XXX) XXX-XXXX."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone
