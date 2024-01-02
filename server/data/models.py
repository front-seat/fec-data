import datetime
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
from server.utils.format import fmt_usd
from server.utils.validations import is_extant_file, validate_extant_file

from .nicknames import split_name

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


class Committee(BaseModel):
    """Represents an FEC committee."""

    __tablename__ = "committees"

    id: sao.Mapped[str] = sao.mapped_column(sa.String(18), primary_key=True)
    name: sao.Mapped[str] = sao.mapped_column(
        sa.String(128), nullable=False, index=True
    )
    party: sao.Mapped[str | None] = sao.mapped_column(
        sa.String(3), nullable=True, default=None
    )
    candidate_id: sao.Mapped[str] = sao.mapped_column(sa.String(18), nullable=True)

    @classmethod
    def from_committee_row(cls, row: t.Sequence[str]) -> t.Self:
        """Create a committee from a row of the committee master file."""
        return cls(
            id=row[CommitteeColumns.ID].strip(),
            name=row[CommitteeColumns.NAME].strip().upper(),
            party=row[CommitteeColumns.PARTY].strip().upper() or None,
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

    @property
    def adjusted_party(self) -> str | None:
        """
        Return the FEC reported party, except in a few key cases,
        where we know better.
        """
        if self.id in KNOWN_DEM_COMMITTEE_IDS:
            return Party.DEMOCRAT
        return self.party

    def to_data(self) -> dict[str, str | None]:
        """Return a dictionary representation of this committee."""
        return {
            "id": self.id,
            "name": self.name,
            "party": self.adjusted_party,
            "candidate_id": self.candidate_id,
        }


class Contribution(BaseModel):
    """Represents a single indvidual FEC contribution."""

    __tablename__ = "contributions"

    id: sao.Mapped[str] = sao.mapped_column(sa.String(18), primary_key=True)
    dt: sao.Mapped[datetime.date] = sao.mapped_column(
        sa.Date, nullable=False, index=True
    )
    committee_id: sao.Mapped[str] = sao.mapped_column(
        sa.String(18), sa.ForeignKey("committees.id"), nullable=False
    )
    committee: sao.Mapped[Committee] = sao.relationship(Committee, lazy="joined")
    last_name: sao.Mapped[str] = sao.mapped_column(sa.String(64), nullable=False)
    first_name: sao.Mapped[str] = sao.mapped_column(sa.String(64), nullable=False)
    city: sao.Mapped[str] = sao.mapped_column(sa.String(64), nullable=False)
    state: sao.Mapped[str] = sao.mapped_column(sa.String(2), nullable=False)
    zip5: sao.Mapped[str] = sao.mapped_column(sa.String(5), nullable=False)
    zip_code: sao.Mapped[str] = sao.mapped_column(sa.String(9), nullable=False)
    employer: sao.Mapped[str] = sao.mapped_column(sa.String(38), nullable=False)
    occupation: sao.Mapped[str] = sao.mapped_column(sa.String(38), nullable=False)
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
        # print(str(statement), last_name, zip_code, first_names)
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
        # print(str(statement), last_name, city, state, first_names)
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
        transaction_dt = row[ContributionColumns.TRANSACTION_DATE].strip()
        try:
            dt = datetime.datetime.strptime(transaction_dt, "%m%d%Y").date()
        except Exception:
            return None
        employer = row[ContributionColumns.EMPLOYER].strip().title() or ""
        occupation = row[ContributionColumns.OCCUPATION].strip().title() or ""
        return cls(
            id=sub_id,
            dt=dt,
            committee_id=committee_id,
            last_name=last_name,
            first_name=first_name,
            city=city,
            state=state,
            zip5=zip_code[:5],
            zip_code=zip_code,
            amount_cents=amount_cents,
            employer=employer,
            occupation=occupation,
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

    def to_data(self) -> dict[str, str | int | None]:
        """Return a dictionary representation of this contribution."""
        return {
            "id": self.id,
            "committee_id": self.committee_id,
            "committee_name": self.committee.name,
            "committee_party": self.committee.adjusted_party,
            "last_name": self.last_name,
            "first_name": self.first_name,
            "city": self.city,
            "state": self.state,
            "zip5": self.zip5,
            "zip_code": self.zip_code,
            "amount_cents": self.amount_cents,
            "amount_fmt": fmt_usd(self.amount_cents),
            "employer": self.employer,
            "occupation": self.occupation,
        }


def is_extant_db(data_manager: DataManager, state: str) -> bool:
    """Return whether or not a database exists for the given data manager."""
    path = data_manager.path / "db" / f"{state}.db"
    return is_extant_file(path)


def validate_extant_db(data_manager: DataManager, state: str) -> None:
    """Validate the existence of a database for the given data manager."""
    path = data_manager.path / "db" / f"{state}.db"
    validate_extant_file(path)


def get_engine(data_manager: DataManager, state: str) -> sa.Engine:
    """Return an engine for the given data manager."""
    return sa.create_engine(
        f"sqlite:///{data_manager.path / 'db' / f'{state}.db'}",
    )


def create_db_tables(engine: sa.Engine) -> None:
    """Create the database tables for the given engine."""
    BaseModel.metadata.create_all(engine)
