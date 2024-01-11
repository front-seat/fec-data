import typing as t

from server.data.contacts import Contact, IContactProvider
from server.data.manager import DataManager
from server.data.models import get_engine, is_extant_db
from server.data.nicknames import NicknamesManager
from server.data.summaries import (
    ContributionSummary,
    ContributionSummaryManager,
)


class ContactContributionSearcher:
    def __init__(self, data_manager: DataManager):
        self._data_manager = data_manager
        self._nicknames_manager = NicknamesManager.from_data_manager(data_manager)
        self._seen = set()
        self._state_to_manager = {}

    def _get_or_load_manager(self, state: str) -> ContributionSummaryManager | None:
        """Get or load a manager for a state."""
        manager = self._state_to_manager.get(state)
        if manager is None:
            if is_extant_db(self._data_manager, state):
                manager = ContributionSummaryManager(
                    get_engine(self._data_manager, state), self._nicknames_manager
                )
                self._state_to_manager[state] = manager
        return manager

    def search_and_summarize(self, contact: Contact) -> ContributionSummary | None:
        """Search for a contact and summarize their contributions."""
        if contact.variant_id in self._seen:
            return None
        if not contact.state:
            return None
        manager = self._get_or_load_manager(contact.state)
        if manager is None:
            return None
        summary = manager.preferred_summary_for_contact(contact)
        if summary is not None:
            self._seen.add(contact.variant_id)
            return summary
        return None

    def search_and_summarize_contacts(
        self, contacts: IContactProvider
    ) -> t.Iterable[tuple[Contact, ContributionSummary | None]]:
        """Search for contacts and summarize their contributions."""
        # Summarize all variants, but line them up with the same import ID.
        import_id_to_summaries: dict[
            str, list[tuple[Contact, ContributionSummary | None]]
        ] = {}
        for contact in contacts.get_contacts():
            result = self.search_and_summarize(contact)
            if result is not None:
                import_id_to_summaries.setdefault(contact.import_id, []).append(
                    (contact, result)
                )
            else:
                import_id_to_summaries.setdefault(contact.import_id, []).append(
                    (contact, None)
                )

        # For each import ID, pick the best summary. That's the one with the
        # largest value *if* there is one; if they're all "None", then it's None.
        for _, summary_tuples in import_id_to_summaries.items():
            best_contact = None
            best_summary = None
            for contact, summary in summary_tuples:
                if summary is None:
                    continue
                if best_summary is None:
                    best_contact = contact
                    best_summary = summary
                elif summary.total_cents > best_summary.total_cents:
                    best_contact = contact
                    best_summary = summary
            if best_contact is None:
                # It doesn't matter which one we choose, since we're unmatched.
                best_contact = summary_tuples[0][0]
            yield best_contact, best_summary
