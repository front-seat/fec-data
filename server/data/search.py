import datetime
import typing as t

from server.data.contacts import Contact, IContactProvider
from server.data.manager import DataManager
from server.data.nicknames import NicknamesManager
from server.data.npa import AreaCodeManager
from server.data.summaries import (
    AlternativeContactsHelper,
    ContributionSummary,
    ContributionSummaryManager,
)
from server.data.usps import ZipCodeManager
from server.utils.bq import BQClient


class ContactContributionSearcher:
    def __init__(
        self, client: BQClient, year: str | datetime.date, data_manager: DataManager
    ):
        self._data_manager = data_manager
        self._nicknames_manager = NicknamesManager.from_data_manager(data_manager)
        self._area_code_manager = AreaCodeManager.from_data_manager(data_manager)
        self._zip_code_manager = ZipCodeManager.from_data_manager(data_manager)
        self._alternatives_helper = AlternativeContactsHelper(
            self._zip_code_manager, self._area_code_manager
        )
        self._seen = set()
        self._contribution_summary_manager = ContributionSummaryManager(
            client, year, self._nicknames_manager
        )

    def search_and_summarize(
        self, contact: Contact
    ) -> tuple[Contact, ContributionSummary] | None:
        """Search for a contact and summarize their contributions."""
        for alternative in self._alternatives_helper.get_alternatives(contact):
            if alternative.duplicate_key in self._seen:
                continue
            state = alternative.state
            assert state
            summary = self._contribution_summary_manager.preferred_summary_for_contact(
                alternative
            )
            if summary is not None:
                return (alternative, summary)
        return None

    def search_and_summarize_contacts(
        self, contacts: IContactProvider
    ) -> t.Iterable[tuple[Contact, ContributionSummary]]:
        """Search for contacts and summarize their contributions."""
        for contact in contacts.get_contacts():
            result = self.search_and_summarize(contact)
            if result is not None:
                yield result
