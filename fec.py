#!/usr/bin/env python3
# ruff: noqa: E501

import json

import click
import sqlalchemy.orm as sao
from tqdm import tqdm

from server.data.contacts import Contact, IContactProvider, SimpleContactProvider
from server.data.contacts.abbu import DirectoryABBUManager, ZipABBUManager
from server.data.manager import DataManager
from server.data.models import (
    Committee,
    Contribution,
    create_db_tables,
    get_engine,
)
from server.data.nicknames import NicknamesManager
from server.data.npa import AreaCodeManager
from server.data.summaries import AlternativeContactsHelper, ContributionSummaryManager
from server.data.usps import ZipCodeManager


@click.group()
def fec():
    """Work with FEC data."""
    pass


@fec.group()
def contacts():
    """Work with contacts data."""
    pass


@contacts.command(name="list")
@click.option(
    "-c",
    "--contact-dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Path to a `.abbu` contacts dir.",
    required=False,
    default=None,
)
@click.option(
    "-z",
    "--contact-zip",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Path to a `.abbu` contacts zip file.",
    required=False,
    default=None,
)
def list_contacts(contact_dir: str | None = None, contact_zip: str | None = None):
    """List contacts."""
    contact_provider: IContactProvider | None = None

    if contact_dir is not None:
        contact_provider = DirectoryABBUManager(contact_dir)
    elif contact_zip is not None:
        contact_provider = ZipABBUManager(contact_zip)

    if contact_provider is None:
        raise click.UsageError(
            "You must provide a contact dir, zip file, or explicit name & zip."
        )

    seen_contacts = set()

    for contact in contact_provider.get_contacts():
        if contact.without_zip() in seen_contacts:
            continue
        seen_contacts.add(contact.without_zip())
        print(json.dumps(contact.to_data()))


@fec.group()
def names():
    """Work with names data."""
    pass


@names.command()
@click.option(
    "--data",
    type=click.Path(exists=True),
    help="Path to data dir.",
    required=False,
    default=None,
)
@click.argument("name", required=True)
def related(name: str, data: str | None = None):
    """Show all related name sets."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    nicknames_manager = NicknamesManager.from_data_manager(data_manager)
    for related_name_set in nicknames_manager.get_related_names(name):
        print(json.dumps(list(related_name_set)))


@fec.group()
def db():
    """Work with the database."""
    pass


@db.command()
@click.option(
    "--data",
    type=click.Path(exists=True),
    help="Path to data dir.",
    required=False,
    default=None,
)
def init(data: str | None = None):
    """Initialize the database."""
    data_manager = DataManager(data) if data is not None else DataManager.default()

    batch_size = 1_000
    state_to_engine = {}
    state_to_buffer = {}

    def _process_buffer(state: str, contributions: list[Contribution]):
        """Add a batch of contributions to the database."""
        # A batch is ready to be added to the database.
        engine = state_to_engine.get(state)

        # Create a new engine if we don't have one for this state, and create
        # the database tables.
        if engine is None:
            engine = get_engine(data_manager, state)
            state_to_engine[state] = engine
            create_db_tables(engine)
            with sao.Session(engine) as session, session.begin():
                session.add_all(Committee.from_data_manager(data_manager))

        # Add the batch to the database.
        with sao.Session(engine) as session, session.begin():
            session.add_all(contributions)

    print("Adding individual contributions...")
    for contribution in tqdm(
        Contribution.from_data_manager(data_manager),
        unit="contribution",
        total=70_659_611,
    ):
        # Queue up contributions by state.
        state = contribution.state
        state_to_buffer.setdefault(state, []).append(contribution)
        if len(state_to_buffer[state]) < batch_size:
            continue

        _process_buffer(state, state_to_buffer[state])
        state_to_buffer[state] = []

    # Add any remaining contributions.
    print("Adding remaining contributions...")
    for state, contributions in state_to_buffer.items():
        if not contributions:
            continue
        _process_buffer(state, contributions)
        state_to_buffer[state] = []

    print("Done.")


@fec.group()
def committees():
    """Work with FEC committees data."""
    pass


@committees.command(name="search")
@click.argument("name")
@click.option(
    "--data",
    type=click.Path(exists=True),
    help="Path to data dir.",
    required=False,
    default=None,
)
def committee_search(name: str, data: str | None = None):
    """Search FEC committees data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    with sao.Session(get_engine(data_manager, "WA")) as session:
        for committee in Committee.for_name(session, name):
            print(json.dumps(committee.to_data(), indent=2))


@fec.group()
def contributions():
    """Work with FEC contributions data."""
    pass


@contributions.command()
@click.argument("first_name", required=False, default=None)
@click.argument("last_name", required=False, default=None)
@click.argument("city", required=False, default=None)
@click.argument("state", required=False, default=None)
@click.argument("zip_code", required=False, default=None)
@click.option(
    "-c",
    "--contact-dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Path to a `.abbu` contacts dir.",
    required=False,
    default=None,
)
@click.option(
    "-z",
    "--contact-zip",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Path to a `.abbu` contacts zip file.",
    required=False,
    default=None,
)
@click.option(
    "--data",
    type=click.Path(exists=True),
    help="Path to data dir.",
    required=False,
    default=None,
)
def search(
    first_name: str | None = None,
    last_name: str | None = None,
    zip_code: str | None = None,
    city: str | None = None,
    state: str | None = None,
    data: str | None = None,
    contact_dir: str | None = None,
    contact_zip: str | None = None,
):
    """Search summarized FEC contributions data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    nicknames_manager = NicknamesManager.from_data_manager(data_manager)
    area_code_manager = AreaCodeManager.from_data_manager(data_manager)
    zip_code_manager = ZipCodeManager.from_data_manager(data_manager)
    alternatives_helper = AlternativeContactsHelper(zip_code_manager, area_code_manager)

    contact_provider: IContactProvider | None = None

    if contact_dir is not None:
        contact_provider = DirectoryABBUManager(contact_dir)
    elif contact_zip is not None:
        contact_provider = ZipABBUManager(contact_zip)
    elif first_name and last_name and city and state:
        singleton = Contact(
            first_name.upper(),
            last_name.upper(),
            city.upper(),
            state.upper(),
            None,
            zip_code,
        )
        contact_provider = SimpleContactProvider([singleton])

    if contact_provider is None:
        raise click.UsageError(
            "You must provide a contact dir, zip file, or explicit name & zip."
        )

    state_to_manager = {}
    seen_contacts = set()

    for contact in contact_provider.get_contacts():
        for alternative in alternatives_helper.get_alternatives(contact):
            if alternative.duplicate_key in seen_contacts:
                continue
            seen_contacts.add(alternative.duplicate_key)

            state = alternative.state
            assert state

            manager = state_to_manager.get(state)
            if manager is None:
                manager = ContributionSummaryManager(
                    get_engine(data_manager, state),
                    nicknames_manager,
                )
                state_to_manager[state] = manager
            summary = manager.preferred_summary_for_contact(alternative)
            if summary is None:
                continue
            print(alternative.first_name.title(), alternative.last_name.title())
            print(str(summary))


if __name__ == "__main__":
    fec()
