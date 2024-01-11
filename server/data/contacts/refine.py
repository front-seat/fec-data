import abc
import typing as t

from server.data.npa import IAreaCodeProvider
from server.data.usps import IZipCodeProvider

from . import Contact, IContactProvider


class ContactProviderWrapper(abc.ABC, IContactProvider):
    """
    An abstract contact provider that wraps another contact provider,
    adjusting the contacts it returns in some way.
    """

    def __init__(self, contact_provider: IContactProvider):
        """Initialize a new instance of the ContactProviderWrapper class."""
        self._contact_provider = contact_provider

    def get_contacts(self) -> t.Iterable[Contact]:
        """Return an iterator of contacts."""
        for contact in self._contact_provider.get_contacts():
            yield from self.wrap_contact(contact)

    @abc.abstractmethod
    def wrap_contact(self, contact: Contact) -> t.Iterable[Contact]:
        """Wrap a contact in some way."""
        ...


class BiasContactProvider(ContactProviderWrapper):
    """
    Implements IContactProvider (see __init__.py) that supports
    'biasing' contacts without a known city/state to a pre-selected
    city/state, or collection of city/states.
    """

    def __init__(
        self, contact_provider: IContactProvider, cities: set[str], states: set[str]
    ):
        """
        Initialize a new instance of the BiasContactProvider class.

        `cities` may be a set of cities, a single city, or the empty set.
        """
        super().__init__(contact_provider)
        self._cities = cities
        assert states, "states must be non-empty"
        self._states = states

    def wrap_contact(self, contact: Contact) -> t.Iterable[Contact]:
        """Wrap a contact in some way."""
        if contact.has_city_state:
            yield contact
        elif self._cities and self._states:
            for city in self._cities:
                for state in self._states:
                    yield contact.with_city_state(city, state)
        else:
            yield contact


class RefineContactProvider(ContactProviderWrapper):
    """
    Implements IContactProvider (see __init__.py) that supports
    'refining' contacts by adding an explicit city + state if we
    are able to uniquely determine them from either the zip code or
    the phone number.

    If we are *not* able to uniquely determine (for instance, an area
    code has multiple cities associated with it), we optionally allow
    spitting out multiple contacts.
    """

    def __init__(
        self,
        contact_provider: IContactProvider,
        area_code_provider: IAreaCodeProvider,
        zip_code_provider: IZipCodeProvider,
    ):
        super().__init__(contact_provider)
        self._area_code_provider = area_code_provider
        self._zip_code_provider = zip_code_provider

    def wrap_contact(self, contact: Contact) -> t.Iterable[Contact]:
        """Return a copy of the contact with the given city and state."""
        if contact.has_city_state:
            yield contact
            return
        if contact.has_zip:
            zip5 = contact.zip5
            assert zip5
            for city, state in self._zip_code_provider.get_city_states(zip5):
                yield contact.with_city_state(city, state)
            return
        if contact.has_us_phone:
            npa_id = contact.npa_id
            assert npa_id
            for area_code in self._area_code_provider.get_area_codes(npa_id):
                if area_code.city and area_code.state:
                    yield contact.with_city_state(area_code.city, area_code.state)
            return
        yield contact
