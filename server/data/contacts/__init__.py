"""Tools for working with contacts lists."""

import typing as t
from dataclasses import dataclass, replace

from server.data.phone import get_npa_id


@dataclass(frozen=True)
class Contact:
    """A contact in the address book."""

    first_name: str
    last_name: str
    city: str | None
    state: str | None
    phone: str | None  # must be in the E164 format
    zip_code: str | None  # Either 5 or 9 digits

    @property
    def zip5(self) -> str | None:
        """Returns the first 5 digits of the zip code, if any."""
        return self.zip_code[:5] if self.zip_code else None

    def to_data(self) -> dict[str, str]:
        """Return a dictionary representation of the contact."""
        data = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "city": self.city,
            "state": self.state,
        }
        if self.phone:
            data["phone"] = self.phone
        if self.npa_id:
            data["npa_id"] = self.npa_id
        if self.zip_code:
            data["zip_code"] = self.zip_code
        return data

    def without_zip(self) -> "Contact":
        """Return a copy of the contact without the zip code."""
        return replace(self, zip_code=None)

    def with_zip(self, zip_code: str) -> "Contact":
        """Return a copy of the contact with the given zip code."""
        return replace(self, zip_code=zip_code)

    def with_city_state(self, city: str, state: str) -> "Contact":
        """Return a copy of the contact with the given city and state."""
        return replace(self, city=city, state=state)

    @property
    def has_zip(self) -> bool:
        """Return True if the contact has a zip code."""
        return self.zip_code is not None

    @property
    def has_phone(self) -> bool:
        """Return True if the contact has a phone number."""
        return self.phone is not None

    @property
    def has_city_state(self) -> bool:
        """Return True if the contact has a city and state."""
        return self.city is not None and self.state is not None

    @property
    def npa_id(self) -> str | None:
        """Return the area code for the contact's phone number."""
        return get_npa_id(self.phone) if self.phone else None

    @property
    def has_us_phone(self) -> bool:
        """Return True if the contact has a US phone number."""
        return self.npa_id is not None

    @property
    def duplicate_key(self) -> tuple[str, str, str, str]:
        """
        Return a 'unique enough' key for the contact.

        Contact keys are used to determine if two contacts are the same.
        """
        assert self.city
        assert self.state
        return (self.first_name, self.last_name, self.city, self.state)


class IContactProvider(t.Protocol):
    """Defines a simple protocol for getting critical contact information."""

    def get_contacts(self) -> t.Iterable[Contact]:
        """Return an iterator of contacts."""
        ...


class SimpleContactProvider:
    """A simple IContactProvider implementation."""

    _contacts: list[Contact]

    def __init__(self, contacts: t.Iterable[Contact]):
        self._contacts = list(contacts)

    def get_contacts(self) -> t.Iterable[Contact]:
        """Return an iterator of contacts."""
        return iter(self._contacts)
