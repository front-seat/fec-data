#!/usr/bin/env python3
# ruff: noqa: E501

import json

import click

from server.data.contacts import Contact, IContactProvider, SimpleContactProvider
from server.data.contacts.abbu import DirectoryABBUManager, ZipABBUManager
from server.data.fec.committees import CommitteeManager
from server.data.fec.contributions import (
    ContributionsManager,
    ContributionSummariesManager,
    FuzzyIdentifier,
)
from server.data.manager import DataManager
from server.data.names.nicknames import MessyNicknamesManager, NicknamesManager


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
def clean(data: str | None = None):
    """Clean raw names data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    messy_names_manager = MessyNicknamesManager.from_data_manager(data_manager)
    nicknames_manager = messy_names_manager.nicknames_manager
    nicknames_manager.to_jsonl_data_manager(data_manager)


@fec.group()
def committees():
    """Work with FEC committees data."""
    pass


@committees.command(name="lookup")
@click.argument("committee_id")
@click.option(
    "--data",
    type=click.Path(exists=True),
    help="Path to data dir.",
    required=False,
    default=None,
)
def committee_lookup(committee_id: str, data: str | None = None):
    """Search FEC committees data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    committees_manager = CommitteeManager.from_csv_data_manager(data_manager)
    committee = committees_manager.get_committee(committee_id)
    if committee is None:
        print("No matching committee.")
    else:
        print(json.dumps(committee.to_data(), indent=2))


@fec.group()
def contributions():
    """Work with FEC contributions data."""
    pass


@contributions.command()
@click.option(
    "--data",
    type=click.Path(exists=True),
    help="Path to data dir.",
    required=False,
    default=None,
)
def summarize(data: str | None = None):
    """Summarize raw FEC individual contribution data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    contributions_manager = ContributionsManager.from_data_manager(data_manager)
    summaries_manager = contributions_manager.contribution_summaries_manager
    summaries_manager.to_jsonl_data_manager(data_manager)


@contributions.command()
@click.argument("first_name", required=False, default=None)
@click.argument("last_name", required=False, default=None)
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
    data: str | None = None,
    contact_dir: str | None = None,
    contact_zip: str | None = None,
):
    """Search summarized FEC contributions data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    nicknames_manager = NicknamesManager.from_data_manager(data_manager)
    summaries_manager = ContributionSummariesManager.from_data_manager(data_manager)

    contact_provider: IContactProvider | None = None

    if contact_dir is not None:
        contact_provider = DirectoryABBUManager(contact_dir)
    elif contact_zip is not None:
        contact_provider = ZipABBUManager(contact_zip)
    elif first_name and last_name and zip_code:
        singleton = Contact(first_name, last_name, zip_code)
        contact_provider = SimpleContactProvider([singleton])

    if contact_provider is None:
        raise click.UsageError(
            "You must provide a contact dir, zip file, or explicit name & zip."
        )

    for contact in contact_provider.get_contacts():
        fuzzy_id = FuzzyIdentifier(
            contact.last,
            contact.first,
            contact.zip_code,
            get_nickname_index=nicknames_manager,
        ).fuzzy_id
        summary = summaries_manager.get_summary(fuzzy_id)
        print(f"--> {contact.first} {contact.last} {contact.zip_code}")
        if summary is None:
            print("{}")
        else:
            print(json.dumps(summary.to_data(), indent=2))


if __name__ == "__main__":
    fec()
