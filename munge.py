#!/usr/bin/env python3
# ruff: noqa: E501

import datetime
import typing as t
from dataclasses import dataclass
from decimal import Decimal

import click

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
    transaction_amount: Decimal  # The amount of the transaction (e.g. 1000.00)
    other_id: str  # The FEC ID of the donor if it is a committee (e.g. C00100005)
    transaction_id: str  # Identifies a single long-running transaction (e.g. SA11A1A.8317)
    file_number: str  # Identifies the electronic or paper report (e.g. 1316462)
    memo_code: str  # 'X' indicates that the amount is not to be included in the itemization total (e.g. X)
    memo_text: str  # A description of the transaction (e.g. "CONTRIBUTION REFUND")
    sub_id: str  # A unique identifier for each itemization (e.g. 4020820181532341437)

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
        return self.name.split(",")[1].strip().upper()


@click.command()
def munge():
    """Munge some FEC data into a more compact form."""
    click.echo("Munging some data")


if __name__ == "__main__":
    munge()
