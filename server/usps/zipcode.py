import csv
import pathlib
import typing as t
from dataclasses import dataclass

from server.data import DataManager
from server.utils.validations import validate_extant_file


@dataclass(frozen=True)
class CityState:
    city: str
    state: str


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
    _city_to_zip_codes: dict[CityState, set[ZipCode]] | None
    _zip5_to_city: dict[str, CityState] | None

    def __init__(self, zip_codes: t.Sequence[ZipCode]) -> None:
        self._zip_codes = list(zip_codes)
        self._city_to_zip_codes = None
        self._zip5_to_city = None

    @classmethod
    def from_csv_io(cls, io: t.TextIO) -> "ZipCodeManager":
        """Return a ZipCodeManager with the given io stream."""
        zip_codes = []
        reader = csv.DictReader(io)
        for row in reader:
            zip_code = ZipCode(
                zip5=row["PHYSICAL ZIP"],
                city=row["PHYSICAL CITY"],
                state=row["PHYSICAL STATE"],
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
        return cls.from_path(data_manager.path / "usps" / "unique-zips.csv")

    def _index_cities(self) -> None:
        assert self._city_to_zip_codes is None
        self._city_to_zip_codes = {}
        for zip_code in self.zip_codes:
            self._city_to_zip_codes.setdefault(zip_code.as_cs(), set()).add(zip_code)

    def _index_cities_if_needed(self) -> None:
        if self._city_to_zip_codes is None:
            self._index_cities()

    def _index_zip5s(self) -> None:
        assert self._zip5_to_city is None
        self._zip5_to_city = {}
        for zip_code in self.zip_codes:
            if zip_code.zip5 not in self._zip5_to_city:
                self._zip5_to_city[zip_code.zip5] = zip_code.as_cs()
            else:
                assert self._zip5_to_city[zip_code.zip5] == zip_code.as_cs()

    def _index_zip5s_if_needed(self) -> None:
        if self._zip5_to_city is None:
            self._index_zip5s()

    @property
    def zip_codes(self) -> list[ZipCode]:
        """Return a list of all unique ZIP codes."""
        return self._zip_codes

    @property
    def city_to_zip_codes(self) -> dict[CityState, set[ZipCode]]:
        """
        Return a dict mapping each city to a set of all unique ZIP
        codes in that city.
        """
        self._index_cities_if_needed()
        assert self._city_to_zip_codes is not None
        return self._city_to_zip_codes

    @property
    def zip5_to_city(self) -> dict[str, CityState]:
        """Return a dict mapping each ZIP5 to the city and state it belongs to."""
        self._index_zip5s_if_needed()
        assert self._zip5_to_city is not None
        return self._zip5_to_city
