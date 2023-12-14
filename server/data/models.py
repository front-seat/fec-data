"""
Tools for working on top of the FEC BigQuery dataset.

See 
https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=fec&page=dataset&project=five-minute-5 
"""

import datetime
import typing as t
from decimal import Decimal

import pydantic as p

from server.data.fec_types import (
    ContributionColumns,
    EntityTypeCode,
    Party,
)
from server.utils.bq import BQClient, Statement, Table

from .nicknames import join_name

# IDs of FEC committees that are known to be Democratic, even if they
# don't report that way in the database. ActBlue is the key example.

KNOWN_DEM_COMMITTEE_IDS = {
    # ActBlue
    "C00401224",
    # Biden Victory Fund
    "C00744946",
    # MoveOn.org Political Action
    "C00341396",
    # Golden Tennis Shoe PAC 2020
    "C00763003",
    # The IMPACT Fund
    "C90020884",
    # Washington Women for Choice
    "C00368332",
    # Movement Voter PAC
    "C00728360",
    # Fair Fight
    "C00693515",
    # EMILY's List
    "C00193433",
    # INDIVISIBLE Action
    "C00678839",
    # National Democratic Redistricting PAC
    "C00630707",
    # ONE FOR ALL Committee
    "C00752691",
}


def get_yy(yy: str | datetime.date) -> str:
    """Return the two-digit year for the given date."""
    return yy.strftime("%y") if isinstance(yy, datetime.date) else yy[-2:]


class Committee(p.BaseModel, frozen=True):
    """Represents an FEC committee."""

    id: str
    name: str | None
    party: str | None
    candidate_id: str | None

    @property
    def adjusted_party(self) -> str | None:
        """
        Return the FEC reported party, except in a few key cases,
        where we know better.
        """
        if self.id in KNOWN_DEM_COMMITTEE_IDS:
            return Party.DEMOCRAT
        return self.party


class CommitteeTable(Table[Committee]):
    """Tools for querying the BigQuery committee master file."""

    def __init__(self, client: BQClient, year: str | datetime.date):
        super().__init__(client, f"cm{get_yy(year)}")

    def get_model_instance(self, row: t.Any) -> Committee:
        """Create a committee from a row of the committee master file."""
        return Committee(
            id=row.cmte_id,
            name=row.cmte_nm,
            party=row.cmte_pty_affiliation,
            candidate_id=row.cand_id,
        )

    def for_name_stmt(self, name: str) -> Statement:
        """Return a select statement for committees matching the given criteria."""
        return self.all_stmt().where("cmte_nm", "LIKE", name.upper())

    def for_name(self, name: str) -> t.Iterable[Committee]:
        """Return a query for committees matching the given criteria."""
        return self.execute(self.for_name_stmt(name))


class Contribution(p.BaseModel, frozen=True):
    """Represents a single indvidual FEC contribution."""

    id: str
    name: str
    city: str
    state: str
    zip_code: str
    amount: Decimal
    committee: Committee


class ContributionTable(Table[Contribution]):
    def __init__(self, client: BQClient, year: str | datetime.date):
        self._committee_table = CommitteeTable(client, year)
        super().__init__(client, f"indiv{get_yy(year)}")

    def all_stmt(self) -> Statement:
        """
        Make the default all_stmt filter to true individuals only and always
        join the committee master file.
        """
        return (
            super()
            .all_stmt()
            .where("entity_tp", "=", "IND")
            .where("amount", ">", 0)
            .join(self._committee_table.name, "cmte_id", "cmte_id")
        )

    def for_last_zip_firsts_stmt(
        self, last_name: str, zip_code: str, first_names: t.Iterable[str]
    ) -> Statement:
        """Return a select statement for contributions matching the given criteria."""
        joined_names = [join_name(last_name, name) for name in first_names]
        return (
            self.all_stmt()
            .where("name", "IN", joined_names)
            .where("zip_code", "=", zip_code[:5])
        )

    def for_last_zip_firsts(
        self, last_name: str, zip_code: str, first_names: t.Iterable[str]
    ) -> t.Iterable[Contribution]:
        """Return a query for contributions matching the given criteria."""
        return self.execute(
            self.for_last_zip_firsts_stmt(last_name, zip_code, first_names)
        )

    def for_last_city_state_firsts_stmt(
        self, last_name: str, city: str, state: str, first_names: t.Iterable[str]
    ):
        """Return a select statement for contributions matching the given criteria."""
        joined_names = [join_name(last_name, name) for name in first_names]
        return (
            self.all_stmt()
            .where("name", "IN", joined_names)
            .where("city", "=", city.upper())
            .where("state", "=", state.upper())
        )

    def for_last_city_state_firsts(
        self,
        last_name: str,
        city: str,
        state: str,
        first_names: t.Iterable[str],
    ) -> t.Iterable[Contribution]:
        """Return a query for contributions matching the given criteria."""
        return self.execute(
            self.for_last_city_state_firsts_stmt(last_name, city, state, first_names)
        )

    def get_model_instance(self, row: t.Any) -> Contribution | None:
        """Insert a contribution from a row of the contributions file."""
        sub_id = row[ContributionColumns.SUB_ID].strip()
        if not sub_id:
            return None
        committee_id = row[ContributionColumns.COMMITTEE_ID].strip()
        if not committee_id:
            return None
        entity_type = row[ContributionColumns.ENTITY_TYPE].strip()
        if entity_type != EntityTypeCode.INDIVIDUAL:
            return None
        name = row[ContributionColumns.NAME].strip()
        if "," not in name:
            return None
        city = row[ContributionColumns.CITY].strip()
        if not city:
            return None
        state = row[ContributionColumns.STATE].strip()
        if not state:
            return None
        zip_code = row[ContributionColumns.ZIP_CODE].strip()
        if len(zip_code) not in {5, 9}:
            return None
        amount = row[ContributionColumns.TRANSACTION_AMOUNT].strip()
        committee = self._committee_table.get_model_instance(row)
        if committee is None:
            return None
        return Contribution(
            id=sub_id,
            committee=committee,
            name=name,
            city=city,
            state=state,
            zip_code=zip_code,
            amount=Decimal(amount),
        )
