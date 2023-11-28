#!/usr/bin/env python3
# ruff: noqa: E501

import json
from itertools import batched

import click
from tqdm import tqdm

from server.data.manager import DataManager
from server.data.models import (
    Committee,
    Contribution,
    create_db_tables,
    engine_for_data_manager,
    session_for_data_manager,
)
from server.data.nicknames import NicknamesManager


@click.group()
def fec():
    """Work with FEC data."""
    pass


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
    print(f"Initializing database for {data_manager.path}.")
    create_db_tables(engine_for_data_manager(data_manager))
    print("Adding committees...")
    with session_for_data_manager(data_manager) as session, session.begin():
        for committee in Committee.from_data_manager(data_manager):
            session.add(committee)
    print("Adding individual contributions...")
    with session_for_data_manager(data_manager) as session:
        for contributions in batched(
            tqdm(
                Contribution.from_data_manager(data_manager),
                unit="contribution",
                total=70_659_611,
            ),
            5_000,
        ):
            with session.begin():
                session.add_all(contributions)
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
    with session_for_data_manager(data_manager) as session:
        for committee in Committee.for_name(session, name):
            print(json.dumps(committee.to_data(), indent=2))


@fec.group()
def contributions():
    """Work with FEC contributions data."""
    pass


# @contributions.command()
# @click.argument("first_name", required=False, default=None)
# @click.argument("last_name", required=False, default=None)
# @click.argument("zip_code", required=False, default=None)
# @click.option(
#     "-c",
#     "--contact-dir",
#     type=click.Path(exists=True, dir_okay=True, file_okay=False),
#     help="Path to a `.abbu` contacts dir.",
#     required=False,
#     default=None,
# )
# @click.option(
#     "-z",
#     "--contact-zip",
#     type=click.Path(exists=True, dir_okay=False, file_okay=True),
#     help="Path to a `.abbu` contacts zip file.",
#     required=False,
#     default=None,
# )
# @click.option(
#     "--data",
#     type=click.Path(exists=True),
#     help="Path to data dir.",
#     required=False,
#     default=None,
# )
# def search(
#     first_name: str | None = None,
#     last_name: str | None = None,
#     zip_code: str | None = None,
#     data: str | None = None,
#     contact_dir: str | None = None,
#     contact_zip: str | None = None,
# ):
#     """Search summarized FEC contributions data."""
#     data_manager = DataManager(data) if data is not None else DataManager.default()
#     nicknames_manager = NicknamesManager.from_data_manager(data_manager)

#     contact_provider: IContactProvider | None = None

#     if contact_dir is not None:
#         contact_provider = DirectoryABBUManager(contact_dir)
#     elif contact_zip is not None:
#         contact_provider = ZipABBUManager(contact_zip)
#     elif first_name and last_name and zip_code:
#         singleton = Contact(first_name, last_name, zip_code)
#         contact_provider = SimpleContactProvider([singleton])

#     if contact_provider is None:
#         raise click.UsageError(
#             "You must provide a contact dir, zip file, or explicit name & zip."
#         )

#     for contact in contact_provider.get_contacts():
#         fuzzy_id = FuzzyIdentifier(
#             contact.last,
#             contact.first,
#             contact.zip_code,
#             get_nickname_index=nicknames_manager,
#         ).fuzzy_id
#         summary = summaries_manager.get_summary(fuzzy_id)
#         print(f"--> {contact.first} {contact.last} {contact.zip_code}")
#         if summary is None:
#             print("{}")
#         else:
#             print(json.dumps(summary.to_data(), indent=2))


if __name__ == "__main__":
    fec()
