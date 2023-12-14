#!/usr/bin/env python3
# ruff: noqa: E501

import json

import click

from server.data.contacts import Contact, IContactProvider, SimpleContactProvider
from server.data.contacts.abbu import DirectoryABBUManager, ZipABBUManager
from server.data.contacts.google import GoogleContactExportManager
from server.data.contacts.linkedin import LinkedInContactsManager
from server.data.manager import DataManager
from server.data.models import CommitteeTable
from server.data.nicknames import NicknamesManager
from server.data.search import ContactContributionSearcher
from server.utils.bq import get_client


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
@click.option(
    "-g",
    "--google",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Path to a Google contacts CSV file.",
    required=False,
    default=None,
)
@click.option(
    "-l",
    "--linkedin",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Path to a LinkedIn contacts CSV file.",
    required=False,
    default=None,
)
def list_contacts(
    contact_dir: str | None = None,
    contact_zip: str | None = None,
    google: str | None = None,
    linkedin: str | None = None,
):
    """List contacts."""
    contact_provider: IContactProvider | None = None

    if contact_dir is not None:
        contact_provider = DirectoryABBUManager(contact_dir)
    elif contact_zip is not None:
        contact_provider = ZipABBUManager(contact_zip)
    elif google is not None:
        contact_provider = GoogleContactExportManager(google)
    elif linkedin is not None:
        contact_provider = LinkedInContactsManager(linkedin)

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
def committees():
    """Work with FEC committees data."""
    pass


@committees.command(name="search")
@click.argument("name")
def committee_search(name: str, data: str | None = None):
    """Search FEC committees data."""
    committee_table = CommitteeTable(get_client(), "2020")
    for committee in committee_table.for_name(name):
        print(json.dumps(committee.model_dump(mode="json"), indent=2))


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
@click.option(
    "-g",
    "--google",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Path to a Google contacts CSV file.",
    required=False,
    default=None,
)
@click.option(
    "-l",
    "--linkedin",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Path to a LinkedIn contacts CSV file.",
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
    google: str | None = None,
    linkedin: str | None = None,
):
    """Search summarized FEC contributions data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    client = get_client()
    searcher = ContactContributionSearcher(client, "2020", data_manager)

    contact_provider: IContactProvider | None = None

    if contact_dir is not None:
        contact_provider = DirectoryABBUManager(contact_dir)
    elif contact_zip is not None:
        contact_provider = ZipABBUManager(contact_zip)
    elif google is not None:
        contact_provider = GoogleContactExportManager(google)
    elif linkedin is not None:
        contact_provider = LinkedInContactsManager(linkedin)
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

    for contact, summary in searcher.search_and_summarize_contacts(contact_provider):
        assert contact.city
        assert contact.state
        print(
            f"{contact.first_name.title()} {contact.last_name.title()} ({contact.city.title()}, {contact.state})"
        )
        print(str(summary))


if __name__ == "__main__":
    fec()
