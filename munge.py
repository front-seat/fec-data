#!/usr/bin/env python3
# ruff: noqa: E501

import datetime
import json
import typing as t
from dataclasses import dataclass
from decimal import Decimal

import click
from tqdm import tqdm

# See https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
type TransactionPGICode = t.Literal[
    "P",  # Primary
    "G",  # General
    "O",  # Other
    "C",  # Convention
    "R",  # Runoff
    "S",  # Special
    "E",  # Recount
]


# See https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
type EntityTypeCode = t.Literal[
    "CAN",  # Candidate
    "CCM",  # Candidate Committee
    "COM",  # Committee
    "IND",  # Individual (a person)
    "ORG",  # Organization (not a committee and not a person)
    "PAC",  # Political Action Committee
    "PTY",  # Party Organization
]


class Nicknames(t.TypedDict):
    """A dictionary of nicknames, keyed by the canonical name."""

    names: list[list[str]]
    indexes: dict[str, int]


@dataclass(frozen=True)
class Committee:
    name: str
    party: str  # Republican, Democrat, or Independent


@dataclass
class MergedContributions:
    total: Decimal
    by_party: dict[str, Decimal]
    by_committee: dict[str, tuple[str, str, Decimal]]

    @classmethod
    def empty(cls) -> "MergedContributions":
        """Create an empty MergedContributions object."""
        return cls(total=Decimal(0), party={}, breakdown={})

    def add(
        self, contribution: "Contribution", committees: dict[str, Committee]
    ) -> None:
        """Add a contribution to this object."""
        self.total += Decimal(contribution.transaction_amount)
        if contribution.committee_id in self.by_committee:
            committee_name, party, amount = self.by_committee[contribution.committee_id]
            amount += Decimal(contribution.transaction_amount)
            self.by_committee[contribution.committee_id] = (
                committee_name,
                party,
                amount,
            )
        else:
            self.by_committee[contribution.committee_id] = (
                committees[contribution.committee_id].name,
                committees[contribution.committee_id].party,
                Decimal(contribution.transaction_amount),
            )
        party_total = self.by_party.get(
            committees[contribution.committee_id].party, Decimal(0)
        )
        party_total += Decimal(contribution.transaction_amount)
        self.by_party[committees[contribution.committee_id].party] = party_total


type ContributorID = tuple[str, str, str]


@dataclass(frozen=True)
class Contribution:
    """
    A single row in an FEC invididual contributions dataset.

    See https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
    """

    committee_id: str  # The FEC ID of the recipient committee (e.g. C00100005)
    amendment_indicator: str  # Whether the contribution is an amendment (e.g. N)
    report_type: str  # The type of report (e.g. Q2 -- see https://www.fec.gov/campaign-finance-data/report-type-code-descriptions/)
    transaction_pgi: str  # Type and cycle of election (e.g. P2018)
    image_number: str  # May be 11-digit or 18-digit format. (e.g. 201810170912345678)
    transaction_type: str  # The type of transaction (see https://www.fec.gov/campaign-finance-data/transaction-type-code-descriptions/)
    entity_type: EntityTypeCode  # The type of entity (e.g. IND)
    name: str  # The contributor's name (e.g. "SMITH, JOHN A")
    city: str  # The contributor's city (e.g. "NEW YORK")
    state: str  # The contributor's state (e.g. "NY")
    zip_code: str  # The contributor's ZIP code + 4 (e.g. "100212021")
    employer: str  # The contributor's employer (e.g. "SELF-EMPLOYED")
    occupation: str  # The contributor's occupation (e.g. "WRITER")
    transaction_date_str: str  # The date of the transaction (e.g. "20180630")
    transaction_amount: str  # The amount of the transaction (e.g. 1000.00)
    other_id: str  # The FEC ID of the donor if it is a committee (e.g. C00100005)
    transaction_id: str  # Identifies a single long-running transaction (e.g. SA11A1A.8317)
    file_number: str  # Identifies the electronic or paper report (e.g. 1316462)
    memo_code: str  # 'X' indicates that the amount is not to be included in the itemization total (e.g. X)
    memo_text: str  # A description of the transaction (e.g. "CONTRIBUTION REFUND")
    sub_id: str  # A unique identifier for each itemization (e.g. 4020820181532341437)

    @property
    def is_individual(self) -> bool:
        """Whether the contributor is an individual."""
        return self.entity_type == "IND"

    @property
    def transaction_pgi_code(self) -> TransactionPGICode:
        """The variety of election (e.g. P for primary)."""
        return t.cast(TransactionPGICode, self.transaction_pgi[0])

    @property
    def transaction_pgi_year(self) -> int:
        """The year of the election (e.g. 2020)."""
        return int(self.transaction_pgi[1:])

    @property
    def transaction_date(self) -> datetime.date:
        """The date of the transaction."""
        return datetime.datetime.strptime(self.transaction_date_str, "%Y%m%d").date()

    @property
    def zip5(self) -> str:
        """The first five digits of the contributor's ZIP code."""
        return self.zip_code[:5]

    @property
    def normalized_last_name(self) -> str:
        """The last name of the contributor, normalized."""
        return self.name.split(",")[0].strip().upper()

    @property
    def normalized_first_name(self) -> str:
        """The first name of the contributor, normalized."""
        try:
            return self.name.split(",")[1].strip().split(" ")[0].strip().upper()
        except IndexError:
            return "UNKNOWN"

    def get_contributor_id(self, nicknames: Nicknames) -> ContributorID:
        """Get a unique identifier for the contributor."""
        last_name = self.normalized_last_name
        first_name = str(
            nicknames["indexes"].get(
                self.normalized_first_name, self.normalized_first_name
            )
        )
        zip5 = self.zip5
        return (last_name, first_name, zip5)

    @classmethod
    def from_line(cls, line: str) -> "Contribution":
        """
        Create a Contribution from a line of text.

        See https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
        """
        (
            committee_id,
            amendment_indicator,
            report_type,
            transaction_pgi,
            image_number,
            transaction_type,
            entity_type,
            name,
            city,
            state,
            zip_code,
            employer,
            occupation,
            transaction_date_str,
            transaction_amount,
            other_id,
            transaction_id,
            file_number,
            memo_code,
            memo_text,
            sub_id,
        ) = line.split("|")
        return cls(
            committee_id=committee_id,
            amendment_indicator=amendment_indicator,
            report_type=report_type,
            transaction_pgi=transaction_pgi,
            image_number=image_number,
            transaction_type=transaction_type,
            entity_type=t.cast(EntityTypeCode, entity_type),
            name=name,
            city=city,
            state=state,
            zip_code=zip_code,
            employer=employer,
            occupation=occupation,
            transaction_date_str=transaction_date_str,
            transaction_amount=transaction_amount,
            other_id=other_id,
            transaction_id=transaction_id,
            file_number=file_number,
            memo_code=memo_code,
            memo_text=memo_text,
            sub_id=sub_id,
        )


@click.command()
@click.argument("fec_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("nicks_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("committees_path", type=click.Path(exists=True, dir_okay=False))
def munge(fec_path: str, nicks_path: str, committees_path: str):
    """
    Munge some FEC data into a more compact form.

    Specifically, we attempt to take the 70M+ rows of individual
    contributions data and reduce it to a more compact form. We seek
    to identify 'unique' donors based on their name and geography. Because
    people use common nicknames, we also use a nicknames file to unify
    those names.
    """
    print("Loading nicknames...", file=click.get_text_stream("stderr"))
    with open(nicks_path) as nicks_file:
        nicknames = t.cast(Nicknames, json.load(nicks_file))

    print("Loading committees...", file=click.get_text_stream("stderr"))
    with open(committees_path) as committees_file:
        committees: dict[str, Committee] = {}
        for line in committees_file:
            split = line.split("|")
            committees[split[0]] = Committee(name=split[1], party=split[10])

    for key, value in list(committees.items())[:5]:
        print(f"{key}: {value}", file=click.get_text_stream("stderr"))

    print("Munging FEC data...", file=click.get_text_stream("stderr"))
    contributors: dict[ContributorID, MergedContributions] = {}
    with open(fec_path) as fec_file:
        for line in tqdm(
            fec_file, desc="Munging FEC data", total=70_659_611, unit="row"
        ):
            contribution = Contribution.from_line(line)
            if not contribution.is_individual:
                continue
            contributor_id = contribution.get_contributor_id(nicknames)
            print(contributor_id, file=click.get_text_stream("stderr"))
            if contributor_id in contributors:
                contributors[contributor_id].add(contribution, committees)
            else:
                contributors[contributor_id] = MergedContributions.empty()
                contributors[contributor_id].add(contribution, committees)

    for key, value in contributors.items():
        str_key = f"{key[0]}-{key[1]}-{key[2]}"
        total = str(value.total)
        party_json_safe = {party: str(amount) for party, amount in value.party.items()}
        breakdown_json_safe = {
            committee_id: [committee_name, party, str(amount)]
            for committee_id, (committee_name, party, amount) in value.breakdown.items()
        }
        jsonable = {
            "id": str_key,
            "total": total,
            "party": party_json_safe,
            "breakdown": breakdown_json_safe,
        }
        print(json.dumps(jsonable))


if __name__ == "__main__":
    munge()
