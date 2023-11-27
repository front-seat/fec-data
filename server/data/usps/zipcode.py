import csv
import pathlib
import typing as t
from dataclasses import dataclass

from server.data.manager import DataManager
from server.utils.validations import validate_extant_file

from .city_state import CityState
from .metros import MajorMetros


@dataclass(frozen=True)
class ZipCode:
    zip5: str
    city: str
    state: str

    def as_cs(self) -> CityState:
        """Return a CityState object with the same city and state as this ZipCode."""
        return CityState(city=self.city, state=self.state)


class ZipCodeManager:
    """Offers methods for managing the raw USPS-supplied unique ZIP code data csv."""

    _zip_codes: list[ZipCode]
    _city_to_zip_codes: dict[CityState, frozenset[ZipCode]] | None
    _zip5_to_cities: dict[str, frozenset[CityState]] | None

    def __init__(self, zip_codes: t.Sequence[ZipCode]) -> None:
        self._zip_codes = list(zip_codes)
        self._city_to_zip_codes = None
        self._zip5_to_cities = None

    @classmethod
    def from_csv_io(cls, io: t.TextIO) -> "ZipCodeManager":
        """Return a ZipCodeManager with the given io stream."""
        zip_codes = []
        reader = csv.DictReader(io)
        for row in reader:
            zip_code = ZipCode(
                zip5=row["PHYSICAL ZIP"],
                city=row["PHYSICAL CITY"].upper().strip(),
                state=row["PHYSICAL STATE"].upper().strip(),
            )
            zip_codes.append(zip_code)
        return cls(zip_codes)

    @classmethod
    def from_path(cls, path: str | pathlib.Path) -> "ZipCodeManager":
        """Return a ZipCodeManager with the given path."""
        path = validate_extant_file(pathlib.Path(path))
        with open(path) as f:
            return cls.from_csv_io(f)

    @classmethod
    def from_data_manager(cls, data_manager: DataManager) -> "ZipCodeManager":
        """Return a ZipCodeManager with the same path as the given DataManager."""
        return cls.from_path(data_manager.path / "usps" / "zips.csv")

    def _index_cities(self) -> None:
        assert self._city_to_zip_codes is None
        unfrozen_city_to_zip_codes: dict[CityState, set[ZipCode]] = {}
        for zip_code in self.zip_codes:
            unfrozen_city_to_zip_codes.setdefault(zip_code.as_cs(), set()).add(zip_code)
        self._city_to_zip_codes = {
            k: frozenset(v) for k, v in unfrozen_city_to_zip_codes.items()
        }

    def _index_cities_if_needed(self) -> None:
        if self._city_to_zip_codes is None:
            self._index_cities()

    def _index_zip5s(self) -> None:
        assert self._zip5_to_cities is None
        unfrozen_zip5_to_cities: dict[str, set[CityState]] = {}
        for zip_code in self.zip_codes:
            unfrozen_zip5_to_cities.setdefault(zip_code.zip5, set()).add(
                zip_code.as_cs()
            )
        self._zip5_to_cities = {
            k: frozenset(v) for k, v in unfrozen_zip5_to_cities.items()
        }

    def _index_zip5s_if_needed(self) -> None:
        if self._zip5_to_cities is None:
            self._index_zip5s()

    @property
    def zip_codes(self) -> t.Sequence[ZipCode]:
        """Return a list of all unique ZIP codes."""
        return self._zip_codes

    @property
    def city_to_zip_codes(self) -> t.Mapping[CityState, frozenset[ZipCode]]:
        """
        Return a dict mapping each city to a set of all unique ZIP
        codes in that city.
        """
        self._index_cities_if_needed()
        assert self._city_to_zip_codes is not None
        return self._city_to_zip_codes

    @property
    def zip5_to_cities(self) -> t.Mapping[str, frozenset[CityState]]:
        """Return a dict mapping each ZIP5 to the city and state it belongs to."""
        self._index_zip5s_if_needed()
        assert self._zip5_to_cities is not None
        return {k: frozenset(v) for k, v in self._zip5_to_cities.items()}

    def get_zip_codes(self, city: str | CityState | None) -> frozenset[ZipCode]:
        """Return a set of all unique ZIP codes in the given city."""
        if isinstance(city, str):
            city = MajorMetros.for_city(city)
        if city is None:
            return frozenset()
        return self.city_to_zip_codes.get(city, frozenset())

    def get_city_states(self, zip5: str) -> frozenset[CityState]:
        """Return all cities and states for the given ZIP5."""
        return self.zip5_to_cities.get(zip5, frozenset())
