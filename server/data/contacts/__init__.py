"""Tools for working with contacts lists."""

import typing as t
from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    """A contact in the address book."""

    first: str
    last: str
    zip_code: str  # Either 5 or 9 digits

    @property
    def zip5(self) -> str:
        """Returns the first 5 digits of the zip code."""
        return self.zip_code[:5]


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
