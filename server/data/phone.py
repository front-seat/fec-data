import phonenumbers


def normalize_e164(phone_number: str) -> str | None:
    """
    Normalize a phone number to E164 format.

    Return None if this cannot be done.
    """
    try:
        # Bias parsing towards US phone numbers since that's what we care about;
        # this will probably fail for non-US numbers in users' contact lists
        # but... oh well.
        parsed = phonenumbers.parse(phone_number, "US")
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(parsed):
        return None
    try:
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return None


def get_npa_id(e164: str) -> str | None:
    """
    Return the area code for an e164-formatted phone number.

    Return None if the phone number is invalid.
    """
    if not e164.startswith("+1"):
        return None
    if len(e164) != 12:
        return None
    return e164[2:5]
