import typing as t

import sqlalchemy as sa
import sqlalchemy.orm as sao

from server.utils.format import fmt_usd

from .contacts import Contact
from .models import Committee, Contribution
from .nicknames import INamesProvider


class ContributionSummary:
    """Provides a high-level summary of multiple contributions."""

    _contributions: list[Contribution]

    def __init__(self, contributions: t.Iterable[Contribution]):
        self._contributions = [
            contribution
            for contribution in contributions
            if contribution.amount_cents > 0
        ]

    @property
    def total_cents(self) -> int:
        """The total amount of all contributions, in cents."""
        return sum(contribution.amount_cents for contribution in self._contributions)

    @property
    def total_fmt(self) -> str:
        """The total amount of all contributions, formatted."""
        return fmt_usd(self.total_cents)

    def committees(self) -> t.Iterable[Committee]:
        """Return the committees that received contributions."""
        return sorted(
            {contribution.committee for contribution in self._contributions},
            key=lambda c: c.name,
        )

    def committee_total_cents(self, committee: Committee) -> int:
        """Return the total amount of contributions for a committee."""
        return sum(
            contribution.amount_cents
            for contribution in self._contributions
            if contribution.committee == committee
        )

    def committee_total_fmt(self, committee: Committee) -> str:
        """Return the total amount of contributions for a committee, formatted."""
        return fmt_usd(self.committee_total_cents(committee))

    def committee_percent(self, committee: Committee) -> float:
        """Return the % of contributions for a committee."""
        return self.committee_total_cents(committee) / self.total_cents

    def parties(self) -> t.Iterable[str]:
        """Return the parties that received contributions."""
        return sorted(
            {contribution.committee.party for contribution in self._contributions}
        )

    def party_total_cents(self, party: str) -> int:
        """Return the total amount of contributions for a party."""
        return sum(
            contribution.amount_cents
            for contribution in self._contributions
            if contribution.committee.party == party
        )

    def party_total_fmt(self, party: str) -> str:
        """Return the total amount of contributions for a party, formatted."""
        return fmt_usd(self.party_total_cents(party))

    def party_percent(self, party: str) -> float:
        """Return the % of contributions for a party."""
        return self.party_total_cents(party) / self.total_cents

    def to_data(self) -> dict:
        """Return a dict representation of the summary."""
        return {
            "total_cents": self.total_cents,
            "total_fmt": self.total_fmt,
            "committees": {
                committee.id: {
                    "name": committee.name,
                    "party": committee.party,
                    "total_cents": self.committee_total_cents(committee),
                    "total_fmt": self.committee_total_fmt(committee),
                    "percent": self.committee_percent(committee),
                }
                for committee in self.committees()
            },
            "parties": {
                party: {
                    "total_cents": self.party_total_cents(party),
                    "total_fmt": self.party_total_fmt(party),
                    "percent": self.party_percent(party),
                }
                for party in self.parties()
            },
        }

    def __str__(self) -> str:
        """Pretty print a summary."""
        lines = []
        lines.append(f"\tTotal: {self.total_fmt}")

        # breakdown by party
        lines.append("\n\tParties:")
        for party in self.parties():
            lines.append(
                f"\t\t{party}: {self.party_total_fmt(party)} ({self.party_percent(party):.2%})"  # noqa: E501
            )

        # breakdown by committee
        lines.append("\n\tCommittees:")
        for committee in self.committees():
            lines.append(
                f"\t\t{committee.name} ({committee.party}): {self.committee_total_fmt(committee)} ({self.committee_percent(committee):.2%})"  # noqa: E501
            )

        return "\n".join(lines)


class ContributionSummaryManager:
    """Tools for building accurate contribution summaries."""

    _engine: sa.Engine
    _names_provider: INamesProvider

    def __init__(self, engine: sa.Engine, names_provider: INamesProvider):
        self._engine = engine
        self._names_provider = names_provider

    def _contact_stmt(self, contact: Contact, related_name_set: frozenset[str]):
        """Return a SQL statement that matches a contact."""
        if contact.zip5 is None:
            return Contribution.for_last_city_state_firsts_stmt(
                contact.last_name,
                contact.city,
                contact.state,
                related_name_set,
            )
        else:
            return Contribution.for_last_zip_firsts_stmt(
                contact.last_name, contact.zip5, related_name_set
            )

    def _summaries_for_contact(
        self, contact: Contact
    ) -> t.Iterable[ContributionSummary]:
        """Return all possible contribution summaries for a contact."""
        related_name_sets = list(
            self._names_provider.get_related_names(contact.first_name)
        )
        with sao.Session(self._engine) as session:
            for related_name_set in related_name_sets:
                stmt = self._contact_stmt(contact, related_name_set)
                summary = ContributionSummary(session.execute(stmt).scalars().all())
                if summary.total_cents > 0:
                    yield summary

    def preferred_summary_for_contact(
        self, contact: Contact
    ) -> ContributionSummary | None:
        """Return the largest contribution summary for a contact."""
        summaries = list(self._summaries_for_contact(contact))
        if not summaries:
            return None
        return max(summaries, key=lambda s: s.total_cents)
