import csv
import pathlib
import typing as t

from server.data.phone import normalize_e164
from server.utils.validations import validate_extant_file

from . import Contact


class GoogleContactExportManager:
    """
    An implementation of IContactProvider (see __init__.py) that supports
    Google's CSV export format.
    """

    def __init__(self, path: str | pathlib.Path):
        self._path = validate_extant_file(pathlib.Path(path))

    def get_contacts(self) -> t.Iterable[Contact]:
        """Return an iterator of contacts."""
        with open(self._path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                first_name = row["Given Name"].strip().upper() or None
                last_name = row["Family Name"].strip().upper() or None
                if not first_name or not last_name:
                    continue
                city = row["Address 1 - City"].strip().upper() or None
                state = row["Address 1 - Region"].strip().upper() or None
                zip_code = (
                    row["Address 1 - Postal Code"].strip().replace("-", "") or None
                )
                if zip_code and len(zip_code) not in {5, 9}:
                    zip_code = None
                phone = normalize_e164(row["Phone 1 - Value"]) or None
                yield Contact(first_name, last_name, city, state, phone, zip_code)
