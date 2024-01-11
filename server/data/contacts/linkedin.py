import csv
import pathlib
import typing as t
import uuid

from server.data.phone import normalize_e164
from server.utils.validations import validate_extant_file

from . import Contact, IContactProvider


class LinkedInContactsManager(IContactProvider):
    """
    Implements IContactProvider (see __init__.py) that supports LinkedIn's
    contacts CSV export format. (Note that LinkedIn also offers 'connections'
    exports, but those don't have enough content to be useful).
    """

    def __init__(self, path: str | pathlib.Path):
        """Initialize a new instance of the LinkedInContactsManager class."""
        self._path = validate_extant_file(pathlib.Path(path))

    def get_contacts(self) -> t.Iterable[Contact]:
        """Return an iterator of contacts."""
        seen_names = set()
        with open(self._path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                source = row["Source"].strip().upper()
                if source == "GOOGLE_CONTACTS":
                    continue
                first_name = row["FirstName"].strip().upper() or None
                last_name = row["LastName"].strip().upper() or None
                if not first_name or not last_name:
                    continue
                if (first_name, last_name) in seen_names:
                    continue
                seen_names.add((first_name, last_name))
                phone_numbers = [pn.strip() for pn in row["PhoneNumbers"].split(",")]
                if not phone_numbers:
                    phone = None
                else:
                    phone = normalize_e164(phone_numbers[0]) or None
                addresses = row["Addresses"].strip()
                address_parts = [ap.strip() for ap in addresses.split(" ")]
                postal_code_parts = [
                    ap for ap in address_parts if ap.startswith("Code:")
                ]
                if not postal_code_parts:
                    zip_code = None
                else:
                    zip_code = postal_code_parts[0].split(":")[1].strip()
                city_parts = [ap for ap in address_parts if ap.startswith("City:")]
                if not city_parts:
                    city = None
                else:
                    city = city_parts[0].split(":")[1].strip().upper()
                state_parts = [ap for ap in address_parts if ap.startswith("State:")]
                if not state_parts:
                    state = None
                else:
                    state = state_parts[0].split(":")[1].strip().upper()
                import_id = str(uuid.uuid4())
                yield Contact(
                    import_id=import_id,
                    first_name=first_name,
                    last_name=last_name,
                    city=city,
                    state=state,
                    phone=phone,
                    zip_code=zip_code,
                )
