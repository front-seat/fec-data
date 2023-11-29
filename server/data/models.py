import csv
import pathlib
import typing as t
from decimal import Decimal

import sqlalchemy as sa
import sqlalchemy.orm as sao

from server.data.fec_types import (
    CommitteeColumns,
    ContributionColumns,
    EntityTypeCode,
    Party,
)
from server.data.manager import DataManager
from server.utils.validations import validate_extant_file

from .nicknames import split_name


class BaseModel(sao.DeclarativeBase):
    """Base class for all SQL models."""

    @classmethod
    def all_stmt(cls):
        """Return a select statement that includes all records."""
        return sa.select(cls)

    @classmethod
    def all(cls, session: sao.Session):
        """Return a query that includes all records."""
        statement = cls.all_stmt()
        return session.execute(statement).scalars()

    @classmethod
    def count(cls, session: sao.Session) -> int:
        """Return the number of failures in the database."""
        id_attr = getattr(cls, "id", None)
        if id_attr is None:
            raise ValueError(f"Model {cls} has no id attribute")
        maybe_result = session.execute(sa.select(sa.func.count(id_attr))).scalar()
        return maybe_result or 0


class ZipCode(BaseModel):
    """
    A 5-digit zip code matched with its city and state.

    Note that a given zip code may be associated with multiple cities and
    states, and a given city and state may be associated with multiple zip
    codes.

    When inserted, cities and states are normalized to uppercase.
    """

    __tablename__ = "zip_codes"

    id: sao.Mapped[int] = sao.mapped_column(primary_key=True)
    zip5: sao.Mapped[str] = sao.mapped_column(sa.String(5), nullable=False, index=True)
    city: sao.Mapped[str] = sao.mapped_column(sa.String(64), nullable=False)
    state: sao.Mapped[str] = sao.mapped_column(sa.String(2), nullable=False)

    # Define indexes. In particular, (zip5, city state) should be unique.
    __table_args__ = (
        sa.Index("zip5_city_state", zip5, city, state, unique=True),
        sa.Index("city_state", city, state),
    )

    @classmethod
    def for_city_and_state_stmt(cls, city: str, state: str):
        """
        Return a select statement that returns all ZipCode records for the
        given city and state.
        """
        return sa.select(cls).where(
            cls.city == city.upper(), cls.state == state.upper()
        )

    @classmethod
    def for_city_and_state(
        cls, session: sao.Session, city: str, state: str
    ) -> t.Iterable[t.Self]:
        """
        Return a query that returns all ZipCode records for the given city and
        state.
        """
        statement = cls.for_city_and_state_stmt(city, state)
        return session.execute(statement).scalars()

    @classmethod
    def for_zip_code_stmt(cls, zip_code: str):
        """
        Return a select statement that returns all ZipCode records for the
        given zip code.
        """
        return sa.select(cls).where(cls.zip5 == zip_code[:5])

    @classmethod
    def for_zip_code(cls, session: sao.Session, zip_code: str) -> t.Iterable[t.Self]:
        """Return a query that returns all ZipCode records for the given zip code."""
        statement = cls.for_zip_code_stmt(zip_code)
        return session.execute(statement).scalars()

    @classmethod
    def from_zip_code_row(cls, row: dict[str, str]) -> t.Self:
        """Create a zip code from a row of the zip code file."""
        return cls(
            zip5=row["PHYSICAL ZIP"][:5],
            city=row["PHYSICAL CITY"].strip().upper(),
            state=row["PHYSICAL STATE"].strip().upper(),
        )

    @classmethod
    def from_csv_io(
        cls,
        text_io: t.TextIO,
    ) -> t.Iterable[t.Self]:
        """Create zip codes from a zip code file."""
        dict_reader = csv.DictReader(text_io)
        return (cls.from_zip_code_row(row) for row in dict_reader)

    @classmethod
    def from_path(
        cls,
        path: pathlib.Path,
    ) -> t.Iterable[t.Self]:
        """Create zip codes from a zip code file on disk."""
        path = validate_extant_file(path)
        with path.open() as file:
            yield from cls.from_csv_io(file)

    @classmethod
    def from_data_manager(
        cls,
        data_manager: DataManager,
    ) -> t.Iterable[t.Self]:
        """Create zip codes from a zip code file."""
        return cls.from_path(data_manager.path / "usps" / "zips.csv")


class Committee(BaseModel):
    """Represents an FEC committee."""

    __tablename__ = "committees"

    id: sao.Mapped[str] = sao.mapped_column(sa.String(18), primary_key=True)
    name: sao.Mapped[str] = sao.mapped_column(
        sa.String(128), nullable=False, index=True
    )
    party: sao.Mapped[str] = sao.mapped_column(sa.String(3), nullable=False)
    candidate_id: sao.Mapped[str] = sao.mapped_column(sa.String(18), nullable=True)

    @classmethod
    def from_committee_row(cls, row: t.Sequence[str]) -> t.Self:
        """Create a committee from a row of the committee master file."""
        return cls(
            id=row[CommitteeColumns.ID].strip(),
            name=row[CommitteeColumns.NAME].strip().upper(),
            party=row[CommitteeColumns.PARTY].strip().upper() or Party.UNKNOWN,
            candidate_id=row[CommitteeColumns.CANDIDATE_ID].strip() or None,
        )

    @classmethod
    def from_csv_io(
        cls,
        text_io: t.TextIO,
    ) -> t.Iterable[t.Self]:
        """Create committees from a FEC committee master file."""
        rows = (row.strip().split("|") for row in text_io)
        return (cls.from_committee_row(row) for row in rows)

    @classmethod
    def from_path(
        cls,
        path: pathlib.Path,
    ) -> t.Iterable[t.Self]:
        """Create committees from a FEC committee master file on disk."""
        path = validate_extant_file(path)
        with path.open() as file:
            yield from cls.from_csv_io(file)

    @classmethod
    def from_data_manager(
        cls,
        data_manager: DataManager,
        year: int = 2020,
    ) -> t.Iterable[t.Self]:
        """Create committees from a FEC committee master file."""
        return cls.from_path(data_manager.path / "fec" / f"committees-{year}.txt")

    @classmethod
    def for_name_stmt(cls, name: str):
        """Return a select statement for committees matching the given criteria."""
        return sa.select(cls).where(cls.name.ilike(f"%{name.upper()}%"))

    @classmethod
    def for_name(
        cls,
        session: sao.Session,
        name: str,
    ) -> t.Iterable[t.Self]:
        """Return a query for committees matching the given criteria."""
        statement = cls.for_name_stmt(name)
        return session.execute(statement).scalars()

    def to_data(self) -> dict[str, str]:
        """Return a dictionary representation of this committee."""
        return {
            "id": self.id,
            "name": self.name,
            "party": self.party,
            "candidate_id": self.candidate_id,
        }


class Contribution(BaseModel):
    """Represents a single indvidual FEC contribution."""

    __tablename__ = "contributions"

    id: sao.Mapped[str] = sao.mapped_column(sa.String(18), primary_key=True)
    committee_id: sao.Mapped[str] = sao.mapped_column(
        sa.String(18), sa.ForeignKey("committees.id"), nullable=False
    )
    committee: sao.Mapped[Committee] = sao.relationship(Committee)
    last_name: sao.Mapped[str] = sao.mapped_column(sa.String(64), nullable=False)
    first_name: sao.Mapped[str] = sao.mapped_column(sa.String(64), nullable=False)
    city: sao.Mapped[str] = sao.mapped_column(sa.String(64), nullable=False)
    state: sao.Mapped[str] = sao.mapped_column(sa.String(2), nullable=False)
    zip5: sao.Mapped[str] = sao.mapped_column(sa.String(5), nullable=False)
    zip_code: sao.Mapped[str] = sao.mapped_column(sa.String(9), nullable=False)
    amount_cents: sao.Mapped[int] = sao.mapped_column(sa.Integer, nullable=False)

    # We need to create indexes on the columns we'll be querying on.
    __table_args__ = (
        sa.Index("last_name_zip5_first_name", last_name, zip5, first_name),
        sa.Index("last_name_city_state_first_name", last_name, city, state, first_name),
    )

    @classmethod
    def for_last_zip_firsts_stmt(
        cls, last_name: str, zip_code: str, first_names: t.Iterable[str]
    ):
        """Return a select statement for contributions matching the given criteria."""
        clean_first_names = [name.upper() for name in first_names]
        if len(clean_first_names) == 1:
            return sa.select(cls).where(
                cls.last_name == last_name.upper(),
                cls.zip5 == zip_code[:5],
                cls.first_name == clean_first_names[0],
            )
        else:
            return sa.select(cls).where(
                cls.last_name == last_name.upper(),
                cls.zip5 == zip_code[:5],
                cls.first_name.in_(clean_first_names),
            )

    @classmethod
    def for_last_zip_firsts(
        cls,
        session: sao.Session,
        last_name: str,
        zip_code: str,
        first_names: t.Iterable[str],
    ) -> t.Iterable[t.Self]:
        """Return a query for contributions matching the given criteria."""
        statement = cls.for_last_zip_firsts_stmt(last_name, zip_code, first_names)
        print(str(statement))
        return session.execute(statement).scalars()

    @classmethod
    def for_last_city_state_firsts_stmt(
        cls, last_name: str, city: str, state: str, first_names: t.Iterable[str]
    ):
        """Return a select statement for contributions matching the given criteria."""
        clean_first_names = [name.upper() for name in first_names]
        if len(clean_first_names) == 1:
            return sa.select(cls).where(
                cls.last_name == last_name.upper(),
                cls.city == city.upper(),
                cls.state == state.upper(),
                cls.first_name == clean_first_names[0],
            )
        else:
            return sa.select(cls).where(
                cls.last_name == last_name.upper(),
                cls.city == city.upper(),
                cls.state == state.upper(),
                cls.first_name.in_(clean_first_names),
            )

    @classmethod
    def for_last_city_state_firsts(
        cls,
        session: sao.Session,
        last_name: str,
        city: str,
        state: str,
        first_names: t.Iterable[str],
    ) -> t.Iterable[t.Self]:
        """Return a query for contributions matching the given criteria."""
        statement = cls.for_last_city_state_firsts_stmt(
            last_name, city, state, first_names
        )
        print(str(statement))
        return session.execute(statement).scalars()

    @classmethod
    def from_contribution_row(cls, row: t.Sequence[str]) -> t.Self | None:
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
        last_name, first_name = split_name(name)
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
            amount_cents = int(Decimal(amount) * 100)
        except Exception:
            return None
        return cls(
            id=sub_id,
            committee_id=committee_id,
            last_name=last_name,
            first_name=first_name,
            city=city,
            state=state,
            zip5=zip_code[:5],
            zip_code=zip_code,
            amount_cents=amount_cents,
        )

    @classmethod
    def from_csv_io(
        cls,
        text_io: t.TextIO,
    ) -> t.Iterable[t.Self]:
        """Create a contributions manager from a FEC individual contributions file."""
        # Turns out this is not simply a CSV with a pipe delimiter. I think it comes
        # down to escaping quotes, but I'm not sure. So we'll just split on pipes.
        rows = (row.strip().split("|") for row in text_io)
        return (
            contribution
            for row in rows
            if (contribution := cls.from_contribution_row(row)) is not None
        )

    @classmethod
    def from_path(
        cls,
        path: pathlib.Path,
    ) -> t.Iterable[t.Self]:
        """Create a contributions manager from a FEC individual contributions file."""
        path = validate_extant_file(path)
        with path.open() as file:
            yield from cls.from_csv_io(file)

    @classmethod
    def from_data_manager(
        cls,
        data_manager: DataManager,
        year: int = 2020,
    ) -> t.Iterable[t.Self]:
        """Create a contributions manager from a FEC individual contributions file."""
        return cls.from_path(data_manager.path / "fec" / f"individual-{year}.txt")

    def to_data(self) -> dict[str, str | int]:
        """Return a dictionary representation of this contribution."""
        return {
            "id": self.id,
            "committee_id": self.committee_id,
            "committee_name": self.committee.name,
            "committee_party": self.committee.party,
            "last_name": self.last_name,
            "first_name": self.first_name,
            "city": self.city,
            "state": self.state,
            "zip5": self.zip5,
            "zip_code": self.zip_code,
            "amount_cents": self.amount_cents,
            "amount_fmt": f"${self.amount_cents / 100:,.2f}",
        }


def get_engine(data_manager: DataManager, state: str) -> sa.Engine:
    """Return an engine for the given data manager."""
    return sa.create_engine(
        f"sqlite:///{data_manager.path / 'db' / f'{state}.db'}",
    )


def create_db_tables(engine: sa.Engine) -> None:
    """Create the database tables for the given engine."""
    BaseModel.metadata.create_all(engine)
