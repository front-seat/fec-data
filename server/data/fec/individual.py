"""
Support reading FEC individual contribution master file content, and
converting it into several derived forms.

You can download per-election-cycle individual contribution master files from:
https://www.fec.gov/data/browse-data/?tab=bulk-data

The schema for the individual contribution master file is available at:
https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
"""
import csv
import json
import pathlib
import typing as t
from dataclasses import dataclass
from decimal import Decimal

from server.data.manager import DataManager
from server.data.names.nicknames import IGetNicknameIndex, NicknamesManager
from server.utils import validations as v

from .committees import CommitteeManager, IGetCommittee


def split_name(name: str) -> tuple[str, str | None]:
    """
    Split a name into a last name and a first name.

    The name should be in the form LAST, FIRST <MIDDLE>. If there is no comma,
    the entire name is assumed to be the last name.
    """
    parts = name.split(",")
    last_name = parts[0].strip()
    first_name = None
    if len(parts) > 1:
        first_name = parts[1].strip().split(" ")[0].strip()
    return (last_name, first_name)


class FuzzyIdentifier:
    """A fuzzy identifier for a contributor."""

    last_name: str
    """The contributor's last name."""

    first_name: str | None
    """The contributor's first name, if known."""

    zip_code: str
    """The contributor's ZIP code, either 5 or 9 digits."""

    _get_nickname_index: IGetNicknameIndex
    _fuzzy_id: str | None

    def __init__(
        self,
        last_name: str,
        first_name: str | None,
        zip_code: str,
        *,
        get_nickname_index: IGetNicknameIndex,
    ):
        self.last_name = last_name
        self.first_name = first_name
        self.zip_code = zip_code
        self._get_nickname_index = get_nickname_index
        self._fuzzy_id = None

    @classmethod
    def from_name(
        cls, name: str, zip_code: str, *, get_nickname_index: IGetNicknameIndex
    ) -> str:
        """Return a fuzzy identifier from a LAST, FIRST style name."""
        last_name, first_name = split_name(name)
        return cls.from_last_first(
            last_name, first_name, zip_code, get_nickname_index=get_nickname_index
        )

    @classmethod
    def from_last_first(
        cls,
        last_name: str,
        first_name: str | None,
        zip_code: str,
        *,
        get_nickname_index: IGetNicknameIndex,
    ) -> str:
        """Return a fuzzy identifier from a LAST, FIRST style name."""
        return cls(
            last_name, first_name, zip_code, get_nickname_index=get_nickname_index
        ).fuzzy_id

    def _nickname_index(self) -> int | None:
        """Return the nickname index for the first name."""
        if self.first_name is None:
            return None
        return self._get_nickname_index.get_index(self.first_name)

    @property
    def _first_nickname(self) -> str | None:
        """Return the first name or nickname."""
        if self.first_name is None:
            return None
        index = self._nickname_index()
        return self.first_name if index is None else str(index)

    def _make_fuzzy_id(self) -> str:
        """Make the fuzzy ID."""
        return f"{self.last_name}-{self._first_nickname}-{self.zip_code}".upper()

    def _make_fuzzy_id_if_needed(self) -> None:
        if self._fuzzy_id is None:
            self._fuzzy_id = self._make_fuzzy_id()

    @property
    def fuzzy_id(self) -> str:
        """Return the fuzzy ID."""
        self._make_fuzzy_id_if_needed()
        assert self._fuzzy_id is not None
        return self._fuzzy_id


class ContributionColumns:
    """
    Column indices for the individual contribution master file.

    See:
    https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
    """

    COMMITTEE_ID = 0  # Filer identification number (CMTE_ID)
    AMENDMENT_INDICATOR = 1  # AMNDT_IND
    REPORT_TYPE = 2  # RPT_TP
    PRIMARY_GENERAL_INDICATOR = 3  # TRANSACTION_PGI
    IMAGE_NUMBER = 4  # IMAGE_NUM
    TRANSACTION_TYPE = 5  # TRANSACTION_TP
    ENTITY_TYPE = 6  # ENTITY_TP (see EntityTypeCode)
    NAME = 7  # NAME (of the contributor, typically in LAST, FIRST <MIDDLE> format)
    CITY = 8  # CITY
    STATE = 9  # STATE
    ZIP_CODE = 10  # ZIP_CODE (usually 5 or 9 digits, but there are lots of odd ones)
    EMPLOYER = 11  # EMPLOYER
    OCCUPATION = 12  # OCCUPATION
    TRANSACTION_DATE = 13  # TRANSACTION_DT (MMDDYYYY)
    TRANSACTION_AMOUNT = 14  # TRANSACTION_AMT (in dollars, NUMBER(14, 2))
    OTHER_ID = 15  # OTHER_ID (for non-individual contributions)
    TRANSACTION_ID = 16  # TRAN_ID
    FILE_NUMBER = 17  # FILE_NUM
    MEMO_CODE = 18  # MEMO_CD
    MEMO_TEXT = 19  # MEMO_TEXT
    SUB_ID = 20  # SUB_ID (FEC record ID)


class EntityTypeCode:
    CANDIDATE = "CAN"
    CANDIDATE_COMMITTEE = "CCM"
    COMMITTEE = "COM"
    INDIVIDUAL = "IND"
    ORGANIZATION = "ORG"
    PAC = "PAC"
    PARTY_ORGANIZATION = "PTY"

    @classmethod
    def name_for_code(cls, code: str) -> str | None:
        """Return the name for the given entity type code."""
        for attr in dir(EntityTypeCode):
            if not attr.startswith("__"):
                if getattr(EntityTypeCode, attr) == code:
                    return attr.replace("_", " ").title()
        return None


@dataclass(frozen=True)
class Contribution:
    """Our simpliciation of an individual contribution."""

    id: str  # The FEC record ID (SUB_ID)
    committee_id: str  # The committee ID (CMTE_ID) contributed to
    name: str  # The contributor's name (NAME)
    city: str  # The contributor's city (CITY)
    state: str  # The contributor's state (STATE)
    zip_code: str  # The contributor's ZIP code (ZIP_CODE) -- 5 or 9 digits
    amount: Decimal

    @property
    def zip5(self) -> str:
        """Return the 5-digit ZIP code."""
        return self.zip_code[:5]

    @classmethod
    def from_contribution_row(cls, row: t.Sequence[str]) -> t.Optional["Contribution"]:
        """
        Create an individual contribution from a row of the committee master file.

        Return None if the contribution is not an individual contribution, or if
        required fields are missing or invalid.
        """
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
        try:
            amount = Decimal(amount)
        except Exception:
            return None
        return cls(
            id=sub_id,
            committee_id=committee_id,
            name=name,
            city=city,
            state=state,
            zip_code=zip_code,
            amount=amount,
        )

    @classmethod
    def from_data(cls, value: t.Any) -> "Contribution":
        """Create an individual contribution from arbitrary data, or raise."""
        data = v.validate_dict(value)
        return cls(
            id=v.get_str(data, "id"),
            committee_id=v.get_str(data, "committee_id"),
            name=v.get_str(data, "name"),
            city=v.get_str(data, "city"),
            state=v.get_str(data, "state"),
            zip_code=v.get_str(data, "zip_code"),
            amount=v.get_convert_decimal(data, "amount"),
        )

    def to_data(self) -> dict:
        """Return the contribution as a dictionary."""
        return {
            "id": self.id,
            "committee_id": self.committee_id,
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "amount": str(self.amount),
        }


@dataclass
class ContributionSummary:
    fuzzy_id: str
    """
    A probably-unique identifier for the contributor.
    
    It should be possible to re-create this from `name` and `zip_code`. However,
    we do not store *all* `name`s that led to this summary record.
    """

    name: str
    """A non-fuzzy name for the contributor."""

    zip_code: str
    """The ZIP code of the contributor."""

    total: Decimal
    """The total amount contributed by the contributor."""

    by_party: dict[str | None, Decimal]
    """Total contributions by party. None is for contributions to unknown parties."""

    by_committee: dict[str, Decimal]
    """Total contributions by committee."""

    @classmethod
    def new(
        cls,
        fuzzy_id: str,
        contribution: Contribution,
        *,
        get_committee: IGetCommittee,
    ) -> "ContributionSummary":
        """Return an empty contribution summary."""
        total = Decimal(contribution.amount)
        committee = get_committee.get_committee(contribution.committee_id)
        party = None if committee is None else committee.party
        by_party = {party: total}
        by_committee = {contribution.committee_id: total}
        return cls(
            fuzzy_id=fuzzy_id,
            name=contribution.name,
            zip_code=contribution.zip_code,
            total=total,
            by_party=by_party,
            by_committee=by_committee,
        )

    def add(self, contribution: Contribution, *, get_committee: IGetCommittee) -> None:
        """Add a single contribution to the summary."""
        self.total += Decimal(contribution.amount)
        committee = get_committee.get_committee(contribution.committee_id)
        party = None if committee is None else committee.party
        self.by_party[party] = self.by_party.get(party, Decimal(0)) + Decimal(
            contribution.amount
        )
        self.by_committee[contribution.committee_id] = self.by_committee.get(
            contribution.committee_id, Decimal(0)
        ) + Decimal(contribution.amount)

    @classmethod
    def from_data(cls, value: t.Any) -> "ContributionSummary":
        """Create a contribution summary from arbitrary data, or raise."""
        data = v.validate_dict(value)
        by_party_data = v.get_dict(data, "by_party")
        by_committee_data = v.get_dict(data, "by_committee")
        return cls(
            fuzzy_id=v.get_str(data, "fuzzy_id"),
            name=v.get_str(data, "name"),
            zip_code=v.get_str(data, "zip_code"),
            total=v.get_convert_decimal(data, "total"),
            by_party={
                party: Decimal(amount) for party, amount in by_party_data.items()
            },
            by_committee={
                committee: Decimal(amount)
                for committee, amount in by_committee_data.items()
            },
        )

    def to_data(self) -> dict:
        """Return a dict representation of the contribution summary."""
        return {
            "fuzzy_id": self.fuzzy_id,
            "name": self.name,
            "zip_code": self.zip_code,
            "total": str(self.total),
            "by_party": {party: str(amount) for party, amount in self.by_party.items()},
            "by_committee": {
                committee: str(amount)
                for committee, amount in self.by_committee.items()
            },
        }


class ContributionsManager:
    """
    Tool for working with raw FEC individual contributions files.

    These are large files, even for a single election cycle. Be warned!
    """

    _contributions: list[Contribution]
    """The raw list of contributions."""

    _get_committee: IGetCommittee
    """A tool for getting committees."""

    _get_nickname_index: IGetNicknameIndex
    """A tool for getting nickname indices."""

    _contribution_summaries: dict[str, ContributionSummary] | None
    """A mapping from fuzzy IDs to contribution summaries."""

    def __init__(
        self,
        contributions: t.Iterable[Contribution],
        get_committee: IGetCommittee,
        get_nickname_index: IGetNicknameIndex,
    ) -> None:
        self._contributions = list(contributions)
        self._contribution_summaries = None
        self._get_committee = get_committee
        self._get_nickname_index = get_nickname_index

    @classmethod
    def from_csv_io(
        cls,
        io: t.TextIO,
        get_committee: IGetCommittee,
        get_nickname_index: IGetNicknameIndex,
    ) -> "ContributionsManager":
        """Create a contributions manager from a FEC individual contributions file."""
        reader = csv.reader(io, delimiter="|")
        contributions = (
            contribution
            for row in reader
            if (contribution := Contribution.from_contribution_row(row)) is not None
        )
        return cls(contributions, get_committee, get_nickname_index)

    @classmethod
    def from_path(
        cls,
        path: str | pathlib.Path,
        get_committee: IGetCommittee,
        get_nickname_index: IGetNicknameIndex,
    ) -> "ContributionsManager":
        """Create a contributions manager from a path."""
        path = v.validate_extant_file(pathlib.Path(path))
        with path.open("rt") as input_file:
            return cls.from_csv_io(input_file, get_committee, get_nickname_index)

    @classmethod
    def from_data_manager(
        cls, data_manager: DataManager, year: int = 2020
    ) -> "ContributionsManager":
        """Create a contributions manager from a data manager."""
        committee_manager = CommitteeManager.from_csv_data_manager(data_manager, year)
        nicknames_manager = NicknamesManager.from_data_manager(data_manager)
        return cls.from_path(
            data_manager.path / "fec" / f"individual-{year}.txt",
            get_committee=committee_manager,
            get_nickname_index=nicknames_manager,
        )

    @property
    def contributions(self) -> t.Sequence[Contribution]:
        """Return the contributions."""
        return self._contributions

    def _summarize_contributions(self) -> None:
        """Summarize the contributions."""
        assert self._contribution_summaries is None
        self._contribution_summaries = {}
        for contribution in self._contributions:
            fuzzy_id = FuzzyIdentifier.from_name(
                contribution.name,
                contribution.zip_code,
                get_nickname_index=self._get_nickname_index,
            )
            if fuzzy_id not in self._contribution_summaries:
                self._contribution_summaries[fuzzy_id] = ContributionSummary.new(
                    fuzzy_id,
                    contribution,
                    get_committee=self._get_committee,
                )
            else:
                self._contribution_summaries[fuzzy_id].add(
                    contribution, get_committee=self._get_committee
                )

    def _summarize_contributions_if_needed(self) -> None:
        if self._contribution_summaries is None:
            self._summarize_contributions()

    @property
    def contribution_summaries(self) -> t.Mapping[str, ContributionSummary]:
        """Return the contribution summaries."""
        self._summarize_contributions_if_needed()
        assert self._contribution_summaries is not None
        return self._contribution_summaries

    @property
    def contribution_summaries_manager(self) -> "ContributionSummariesManager":
        """Get the affiliated contribution summaries manager."""
        return ContributionSummariesManager(self.contribution_summaries)


class ContributionSummariesManager:
    """
    Tool for working with summarized FEC individual contributions files.

    These are large files, even for a single election cycle. Be warned!
    """

    _contribution_summaries: dict[str, ContributionSummary]
    """A mapping from fuzzy IDs to contribution summaries."""

    def __init__(
        self, contribution_summaries: t.Mapping[str, ContributionSummary]
    ) -> None:
        self._contribution_summaries = dict(contribution_summaries)

    @classmethod
    def from_jsonl_io(cls, io: t.TextIO) -> "ContributionSummariesManager":
        """
        Read from a json lines file and create a manager.

        The file contains a single ContributionSummary record on each line.
        The `fuzzy_id` fields must be unique across the entire dataset.
        """
        summaries = (json.loads(line) for line in io)
        return cls({summary.fuzzy_id: summary for summary in summaries})

    @classmethod
    def from_path(cls, path: str | pathlib.Path) -> "ContributionSummariesManager":
        """Create a contribution summaries manager from a path."""
        path = v.validate_extant_file(pathlib.Path(path))
        with path.open("rt") as input_file:
            return cls.from_jsonl_io(input_file)

    @classmethod
    def from_data_manager(
        cls, data_manager: DataManager, year: int = 2020
    ) -> "ContributionSummariesManager":
        """Create a contribution summaries manager from a data manager."""
        return cls.from_path(
            data_manager.path / "fec" / f"contribution-summaries-{year}.jsonl",
        )

    def to_data_lines(self) -> t.Iterable[dict]:
        """Convert to a json-serializable object."""
        return (summary.to_data() for summary in self._contribution_summaries.values())

    def to_jsonl_io(self, io: t.TextIO) -> None:
        """Write to a json lines file."""
        for data_line in self.to_data_lines():
            io.write(json.dumps(data_line))
            io.write("\n")

    def to_jsonl_path(self, path: str | pathlib.Path) -> None:
        """Write to a json lines file."""
        path = pathlib.Path(path)
        with path.open("wt") as output_file:
            self.to_jsonl_io(output_file)

    def to_jsonl_data_manager(
        self, data_manager: DataManager, year: int = 2020
    ) -> None:
        """Write to a json lines file."""
        self.to_jsonl_path(
            data_manager.path / "fec" / f"contribution-summaries-{year}.jsonl"
        )

    @property
    def contribution_summaries(self) -> t.Mapping[str, ContributionSummary]:
        """Return the contribution summaries."""
        return self._contribution_summaries

    def get_summary(self, fuzzy_id: str) -> ContributionSummary | None:
        """Return a single contribution summary, if available."""
        return self._contribution_summaries.get(fuzzy_id)
