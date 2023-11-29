"""Tools for working with contacts lists."""

import typing as t
from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    """A contact in the address book."""

    first_name: str
    last_name: str
    city: str
    state: str
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
        if self.zip_code:
            data["zip_code"] = self.zip_code
        return data


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
