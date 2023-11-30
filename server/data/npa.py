import csv
import pathlib
import typing as t
from dataclasses import dataclass

from server.utils.validations import get_str, validate_dict, validate_extant_file

from .manager import DataManager


@dataclass(frozen=True)
class AreaCode:
    """A phone number area code aka NAMPA NPA_ID."""

    npa_id: str
    city: str
    state: str

    @classmethod
    def from_data(cls, d: t.Any) -> t.Self:
        """Create an AreaCode from a data object."""
        data = validate_dict(d)
        return cls(
            npa_id=get_str(data, "area_code"),
            city=get_str(data, "city"),
            state=get_str(data, "state"),
        )

    def to_data(self) -> dict[str, str]:
        """Convert the AreaCode to a data object."""
        return {
            "area_code": self.npa_id,
            "city": self.city,
            "state": self.state,
        }


class IAreaCodeProvider(t.Protocol):
    """A protocol for providing area codes."""

    def get_area_codes(self, npa_id: str) -> t.Iterable[AreaCode]:
        """Get all area codes for a given NPA_ID."""
        ...

    def get_city_states(self, npa_id: str) -> t.Iterable[tuple[str, str]]:
        """Get all city, state pairs for a given NPA_ID."""
        ...


class AreaCodeManager:
    """Tools for working with phone number area codes aka NAMPA NPA_IDs."""

    _area_codes: list[AreaCode]
    _npa_id_to_area_codes: dict[str, frozenset[AreaCode]]

    def __init__(self, area_codes: t.Iterable[AreaCode]):
        self._area_codes = list(area_codes)

        # Index the area codes by NPA_ID.
        unfrozen_npa_id_to_area_codes: dict[str, set[AreaCode]] = {}
        for area_code in self._area_codes:
            unfrozen_npa_id_to_area_codes.setdefault(area_code.npa_id, set()).add(
                area_code
            )
        self._npa_id_to_area_codes = {
            npa_id: frozenset(area_codes)
            for npa_id, area_codes in unfrozen_npa_id_to_area_codes.items()
        }

    @property
    def area_codes(self) -> t.Sequence[AreaCode]:
        """All area codes."""
        return self._area_codes

    @property
    def npa_ids(self) -> t.Sequence[str]:
        """All NPA_IDs."""
        return list(self._npa_id_to_area_codes.keys())

    def get_area_codes(self, npa_id: str) -> t.Iterable[AreaCode]:
        """Get all area codes for a given NPA_ID."""
        return self._npa_id_to_area_codes.get(npa_id, [])

    def get_city_states(self, npa_id: str) -> t.Iterable[tuple[str, str]]:
        """Get all city, state pairs for a given NPA_ID."""
        return (
            (area_code.city, area_code.state)
            for area_code in self.get_area_codes(npa_id)
        )

    @classmethod
    def from_csv_io(cls, csv_io: t.TextIO) -> t.Self:
        """Create an AreaCodeManager from a CSV file."""
        reader = csv.DictReader(csv_io)
        return cls(AreaCode.from_data(row) for row in reader)

    @classmethod
    def from_csv_path(cls, path: str | pathlib.Path) -> t.Self:
        """Create an AreaCodeManager from a CSV path."""
        path = validate_extant_file(pathlib.Path(path))
        with path.open("rt") as input_file:
            return cls.from_csv_io(input_file)

    @classmethod
    def from_data_manager(cls, data_manager: DataManager) -> t.Self:
        """Create an AreaCodeManager from a data manager."""
        return cls.from_csv_path(data_manager.path / "npa" / "npa_details.csv")
