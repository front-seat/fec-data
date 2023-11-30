import csv
import pathlib
import typing as t
from dataclasses import dataclass

from server.utils.validations import validate_extant_file

from .manager import DataManager


@dataclass(frozen=True)
class ZipCodeDetail:
    zip5: str
    city: str
    state: str

    @classmethod
    def from_zip_code_row(cls, row: dict[str, str]) -> t.Self:
        """Create a zip code from a row of the zip code file."""
        return cls(
            zip5=row["PHYSICAL ZIP"][:5],
            city=row["PHYSICAL CITY"].strip().upper(),
            state=row["PHYSICAL STATE"].strip().upper(),
        )


class IZipCodeProvider(t.Protocol):
    """Interface for zip code providers."""

    def get_details(self, zip_code: str) -> t.Iterable[ZipCodeDetail]:
        """Return all zip code details for a zip code."""
        ...

    def get_city_states(self, zip_code: str) -> t.Iterable[tuple[str, str]]:
        """Return all city, state pairs for a zip code."""
        ...


class ZipCodeManager:
    """Tools for managing zip code data."""

    _details: list[ZipCodeDetail]
    _zip5_to_details: dict[str, frozenset[ZipCodeDetail]]

    def __init__(self, details: t.Iterable[ZipCodeDetail]):
        self._details = list(details)

        # Index the zip codes by zip5
        unfrozen_zip5_to_details = {}
        for detail in self._details:
            unfrozen_zip5_to_details.setdefault(detail.zip5, set()).add(detail)
        self._zip5_to_details = {
            zip5: frozenset(details)
            for zip5, details in unfrozen_zip5_to_details.items()
        }

    @property
    def details(self) -> t.Iterable[ZipCodeDetail]:
        """Return all zip codes."""
        return self.details

    def get_details(self, zip_code: str) -> t.Iterable[ZipCodeDetail]:
        """Return all zip code details for a zip code."""
        if len(zip_code) not in (5, 9):
            return frozenset()
        return sorted(
            self._zip5_to_details.get(zip_code[:5], frozenset()),
            key=lambda detail: detail.city,
        )

    def get_city_states(self, zip_code: str) -> t.Iterable[tuple[str, str]]:
        """Return all city, state pairs for a zip code."""
        return ((detail.city, detail.state) for detail in self.get_details(zip_code))

    @classmethod
    def from_csv_io(
        cls,
        text_io: t.TextIO,
    ) -> t.Self:
        """Create zip codes from a zip code file."""
        reader = csv.DictReader(text_io)
        details = {ZipCodeDetail.from_zip_code_row(row) for row in reader}
        return cls(details)

    @classmethod
    def from_path(
        cls,
        path: pathlib.Path,
    ) -> t.Self:
        """Create zip codes from a zip code file on disk."""
        path = validate_extant_file(path)
        with path.open() as file:
            return cls.from_csv_io(file)

    @classmethod
    def from_data_manager(
        cls,
        data_manager: DataManager,
    ) -> t.Self:
        """Create zip codes from a zip code file."""
        return cls.from_path(data_manager.path / "usps" / "zips.csv")
