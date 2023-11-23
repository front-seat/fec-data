"""
Support reading FEC committee master file content.

You can download per-election-cycle committee master files from:
https://www.fec.gov/data/browse-data/?tab=bulk-data

The schema for the committee master file is available at:
https://www.fec.gov/campaign-finance-data/committee-master-file-description/
"""
import csv
import json
import pathlib
import typing as t
from dataclasses import dataclass

from server.data.manager import DataManager
from server.utils import validations as v


class CommitteeTypeCode:
    """
    Committee type codes.

    See:
    https://www.fec.gov/campaign-finance-data/committee-type-code-descriptions/
    """

    COMMUNICATION_COST = "C"
    DELEGATE_COMMITTEE = "D"
    ELECTIONEERING_COMMUNICATION = "E"
    HOUSE = "H"
    INDEPEDENT_PERSON_OR_GROUP = "I"
    PAC_NONQUALIFIED = "N"
    INDEPEDENT_SUPER_PAC = "O"
    PRESIDENTIAL = "P"
    PAC_QUALIFIED = "Q"
    SENATE = "S"
    SINGLE_CANDIDATE_INDEPENDENT_EXPENDITURE = "U"
    HYBRID_PAC_NONQUALIFIED = "V"
    HYBRID_PAC_QUALIFIED = "W"
    PARTY_NONQUALIFIED = "X"
    PARTY_QUALIFIED = "Y"
    NATIONAL_PARTY_NONFEDERAL = "Z"

    @classmethod
    def name_for_code(cls, code: str) -> str | None:
        """Return the name for the given committee type code."""
        for attr in dir(CommitteeTypeCode):
            if not attr.startswith("__"):
                if getattr(CommitteeTypeCode, attr) == code:
                    return attr.replace("_", " ").title()
        return None


class CommitteeColumns:
    """
    Column indices for the committee master file.

    See:
    https://www.fec.gov/campaign-finance-data/committee-master-file-description/
    """

    ID = 0  # CMTE_ID
    NAME = 1  # CMTE_NM
    TREASURER_NAME = 2  # TRES_NM
    STREET_1 = 3  # CMTE_ST1
    STREET_2 = 4  # CMTE_ST2
    CITY = 5  # CMTE_CITY
    STATE = 6  # CMTE_ST
    ZIP_CODE = 7  # CMTE_ZIP
    DESIGNATION = 8  # CMTE_DSGN
    TYPE = 9  # CMTE_TP
    PARTY = 10  # CMTE_PTY_AFFILIATION
    ORG_TYPE = 11  # ORG_TP
    CONNECTED_ORG_NAME = 12  # CONNECTED_ORG_NM
    CANDIDATE_ID = 13  # CAND_ID


class Party:
    """
    Political party codes.

    For an (incredibly) exhaustive list, see:
    https://www.fec.gov/campaign-finance-data/party-code-descriptions/
    """

    REPUBLICAN = "REP"
    DEMOCRAT = "DEM"
    INDEPENDENT = "IND"
    LIBERTARIAN = "LIB"
    GREEN = "GRE"
    UNKNOWN = "UNK"  # We specifically ignore this/convert to None

    @classmethod
    def name_for_code(cls, code: str) -> str | None:
        """Return the name for the given party code."""
        for attr in dir(Party):
            if not attr.startswith("__"):
                if getattr(Party, attr) == code:
                    return attr.title()
        return None


@dataclass(frozen=True)
class Committee:
    """Our simplification of the committee record."""

    id: str
    name: str
    party: str | None
    candidate_id: str | None

    @classmethod
    def from_committee_row(cls, row: t.Sequence[str]) -> "Committee":
        """Create a committee from a row of the committee master file."""
        data = {
            "id": row[CommitteeColumns.ID].strip(),
            "name": row[CommitteeColumns.NAME].strip(),
        }
        party = row[CommitteeColumns.PARTY].strip().upper()
        if party and party != Party.UNKNOWN:
            data["party"] = party
        candidate_id = row[CommitteeColumns.CANDIDATE_ID].strip()
        if candidate_id:
            data["candidate_id"] = candidate_id
        return cls.from_data(data)

    @classmethod
    def from_data(cls, value: t.Any) -> "Committee":
        """Create a committee from arbitrary data, or raise an exception."""
        data = v.validate_dict(value)
        return cls(
            id=v.get_str(data, "id"),
            name=v.get_str(data, "name"),
            party=v.get_optional_str(data, "party"),
            candidate_id=v.get_optional_str(data, "candidate_id"),
        )

    def to_data(self) -> dict:
        """Return a dict representation of the committee."""
        data = {
            "id": self.id,
            "name": self.name,
        }
        if self.party is not None:
            data["party"] = self.party
        if self.candidate_id is not None:
            data["candidate_id"] = self.candidate_id
        return data


class IGetCommittee(t.Protocol):
    """Interface for getting a committee."""

    def get_committee(self, id: str) -> Committee | None:
        """Get the committee with the given id, or None."""
        ...


class MockGetCommittee(IGetCommittee):
    """A mock implementation of IGetCommittee."""

    _id_to_committee: dict[str, Committee]

    def __init__(self, committees: t.Sequence[Committee]) -> None:
        """Create a mock implementation."""
        self._id_to_committee = {committee.id: committee for committee in committees}

    def get_committee(self, id: str) -> Committee | None:
        """Get the committee with the given id, or None."""
        return self._id_to_committee.get(id)


class CommitteeManager:
    """Manages a collection of committees."""

    _committees: list[Committee]
    _id_to_committee: dict[str, Committee] | None

    def __init__(self, committees: t.Iterable[Committee]) -> None:
        """Create a committee manager."""
        self._committees = list(committees)
        self._id_to_committee = None

    @classmethod
    def from_csv_io(cls, io: t.TextIO) -> "CommitteeManager":
        """Create a committee manager from a CSV file."""
        reader = csv.reader(io, delimiter="|")
        return cls(Committee.from_committee_row(row) for row in reader)

    @classmethod
    def from_csv_path(cls, path: pathlib.Path) -> "CommitteeManager":
        """Create a committee manager from a CSV file."""
        path = v.validate_extant_file(path)
        with path.open() as file:
            return cls.from_csv_io(file)

    @classmethod
    def from_csv_data_manager(
        cls, data_manager: "DataManager", year: int = 2020
    ) -> "CommitteeManager":
        """Create a committee manager from a data manager."""
        return cls.from_csv_path(data_manager.path / "fec" / f"committees-{year}.txt")

    @classmethod
    def from_jsonl_io(cls, io: t.TextIO) -> "CommitteeManager":
        """Create a committee manager from a json-lines file."""
        return cls(Committee.from_data(json.loads(line)) for line in io)

    @classmethod
    def from_jsonl_path(cls, path: pathlib.Path) -> "CommitteeManager":
        """Create a committee manager from a json-lines file."""
        path = v.validate_extant_file(path)
        with path.open() as file:
            return cls.from_jsonl_io(file)

    @classmethod
    def from_jsonl_data_manager(
        cls, data_manager: "DataManager", year: int = 2020
    ) -> "CommitteeManager":
        """Create a committee manager from a data manager."""
        return cls.from_jsonl_path(
            data_manager.path / "fec" / f"committees-{year}.jsonl"
        )

    def to_data_lines(self) -> t.Iterable[dict]:
        """Convert to a list of json-serializable objects."""
        return (committee.to_data() for committee in self._committees)

    def to_jsonl_io(self, io: t.TextIO) -> None:
        """Write to a json file."""
        for data_line in self.to_data_lines():
            io.write(json.dumps(data_line))
            io.write("\n")

    def to_jsonl_path(self, path: pathlib.Path) -> None:
        """Write to a json file."""
        with path.open("wt") as output_file:
            self.to_jsonl_io(output_file)

    def to_jsonl_data_manager(
        self, data_manager: "DataManager", year: int = 2020
    ) -> None:
        """Write to a json file."""
        self.to_jsonl_path(data_manager.path / "fec" / f"committees-{year}.jsonl")

    def _index_committees(self) -> None:
        """Index the committees by id."""
        assert self._id_to_committee is None
        self._id_to_committee = {}
        for committee in self._committees:
            assert committee.id not in self._id_to_committee
            self._id_to_committee[committee.id] = committee

    def _index_committees_if_needed(self) -> None:
        """Index the committees by id if needed."""
        if self._id_to_committee is None:
            self._index_committees()

    @property
    def committees(self) -> t.Sequence[Committee]:
        """Get the list of committees."""
        return self._committees

    @property
    def id_to_committee(self) -> t.Mapping[str, Committee]:
        """Get the mapping from id to committee."""
        self._index_committees_if_needed()
        assert self._id_to_committee is not None
        return self._id_to_committee

    def get_committee(self, id: str) -> Committee | None:
        """Get the committee with the given id, or None."""
        return self.id_to_committee.get(id)
