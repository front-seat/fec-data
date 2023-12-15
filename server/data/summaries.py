import datetime
import typing as t
from decimal import Decimal

from server.utils.bq import BQClient

from .contacts import Contact
from .models import Committee, Contribution, ContributionTable
from .nicknames import INamesProvider
from .npa import IAreaCodeProvider
from .usps import IZipCodeProvider


class ContributionSummary:
    """Provides a high-level summary of multiple contributions."""

    _contributions: list[Contribution]

    def __init__(self, contributions: t.Iterable[Contribution]):
        self._contributions = list(contributions)

    @property
    def total(self) -> Decimal:
        """The total amount of all contributions, in USD."""
        return sum(
            contribution.amount for contribution in self._contributions
        ) or Decimal(0)

    def committees(self) -> t.Iterable[Committee]:
        """Return the committees that received contributions."""
        return {contribution.committee for contribution in self._contributions}

    def committee_total(self, committee: Committee) -> Decimal:
        """Return the total amount of contributions for a committee."""
        return sum(
            contribution.amount
            for contribution in self._contributions
            if contribution.committee == committee
        ) or Decimal(0)

    def committee_percent(self, committee: Committee) -> float:
        """Return the % of contributions for a committee."""
        return float(self.committee_total(committee) / self.total)

    def parties(self) -> t.Iterable[str | None]:
        """Return the parties that received contributions."""
        return {
            contribution.committee.adjusted_party
            for contribution in self._contributions
        }

    def party_total(self, party: str | None) -> Decimal:
        """Return the total amount of contributions for a party."""
        return sum(
            contribution.amount
            for contribution in self._contributions
            if contribution.committee.adjusted_party == party
        ) or Decimal(0)

    def party_percent(self, party: str | None) -> float:
        """Return the % of contributions for a party."""
        return float(self.party_total(party) / self.total)

    def to_data(self) -> dict:
        """Return a dict representation of the summary."""
        return {
            "total": self.total,
            "committees": {
                committee.id: {
                    "name": committee.name,
                    "party": committee.adjusted_party,
                    "total_cents": self.committee_total(committee),
                    "percent": self.committee_percent(committee),
                }
                for committee in self.committees()
            },
            "parties": {
                party: {
                    "total_cents": self.party_total(party),
                    "percent": self.party_percent(party),
                }
                for party in self.parties()
            },
        }

    def __str__(self) -> str:
        """Pretty print a summary."""
        lines = []
        lines.append(f"\tTotal: {self.total}")

        # breakdown by party
        lines.append("\n\tParties:")
        for party in self.parties():
            lines.append(
                f"\t\t{party}: {self.party_total(party)} ({self.party_percent(party):.2%})"  # noqa: E501
            )

        # breakdown by committee
        lines.append("\n\tCommittees:")
        for committee in self.committees():
            lines.append(
                f"\t\t{committee.name} ({committee.adjusted_party}): {self.committee_total(committee)} ({self.committee_percent(committee):.2%})"  # noqa: E501
            )

        return "\n".join(lines)


class AlternativeContactsHelper:
    """Tools for finding and refining contact details."""

    def __init__(
        self, zip_code_provider: IZipCodeProvider, area_code_provider: IAreaCodeProvider
    ):
        self._zip_code_provider = zip_code_provider
        self._area_code_provider = area_code_provider

    def get_alternatives(
        self,
        contact: Contact,
    ) -> t.Iterable[Contact]:
        """Return useful alternative contacts for a given contact."""
        # If the contact has a city + state, we're done.
        if contact.has_city_state:
            yield contact
            return

        # If the contact has a zip code, but no city + state, then we need to
        # find the city + state from the zip code.
        zip_code = contact.zip_code
        if zip_code is not None:
            for city, state in self._zip_code_provider.get_city_states(zip_code):
                yield contact.with_city_state(city, state)
            return

        # If the contact has a US area code, but no city + state, then we need
        # to find the city + state from the area code.
        npa_id = contact.npa_id
        if npa_id is not None:
            for city, state in self._area_code_provider.get_city_states(npa_id):
                yield contact.with_city_state(city, state)

        # It's possible that no searchable alternatives for this contact exist.
        # So be it.
        return


class ContributionSummaryManager:
    """Tools for building accurate contribution summaries."""

    _names_provider: INamesProvider

    def __init__(
        self,
        client: BQClient,
        year: str | datetime.date,
        names_provider: INamesProvider,
    ):
        self._contribution_table = ContributionTable(client, year)
        self._names_provider = names_provider

    def _contributions(
        self, contact: Contact, related_name_set: frozenset[str]
    ) -> t.Iterable[Contribution]:
        """Return an iterable of contributions that match a contact."""
        if contact.zip5 is None:
            assert contact.city
            assert contact.state
            return self._contribution_table.for_last_city_state_firsts(
                contact.last_name,
                contact.city,
                contact.state,
                related_name_set,
            )
        else:
            return self._contribution_table.for_last_zip_firsts(
                contact.last_name, contact.zip5, related_name_set
            )

    def _summaries_for_contact(self, contact: Contact) -> list[ContributionSummary]:
        """Return all possible contribution summaries for a contact."""
        related_name_sets = list(
            self._names_provider.get_related_names(contact.first_name)
        )
        # No related names? Just use the first name.
        if not related_name_sets:
            related_name_sets = [frozenset([contact.first_name])]
        summaries = []
        for related_name_set in related_name_sets:
            contributions = self._contributions(contact, related_name_set)
            summary = ContributionSummary(contributions)
            if summary.total > 0:
                summaries.append(summary)
        return summaries

    def preferred_summary_for_contact(
        self, contact: Contact
    ) -> ContributionSummary | None:
        """Return the largest contribution summary for a contact."""
        assert contact.has_city_state
        try_contacts = [contact]
        if contact.has_zip:
            try_contacts.append(contact.without_zip())

        summaries = []
        for try_contact in try_contacts:
            summaries.extend(self._summaries_for_contact(try_contact))

        if not summaries:
            return None
        return max(summaries, key=lambda s: s.total)
