#!/usr/bin/env python3
# ruff: noqa: E501

import csv
import io
import json
import typing as t

import click
import pandas as pd
import sqlalchemy.orm as sao
from tqdm import tqdm

from server.data.contacts import Contact, IContactProvider, SimpleContactProvider
from server.data.contacts.abbu import DirectoryABBUManager, ZipABBUManager
from server.data.contacts.google import GoogleContactExportManager
from server.data.contacts.linkedin import LinkedInContactsManager
from server.data.manager import DataManager
from server.data.models import (
    Committee,
    Contribution,
    create_db_tables,
    get_engine,
)
from server.data.nicknames import NicknamesManager
from server.data.search import ContactContributionSearcher
from server.data.summaries import ContributionSummary


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
@click.option(
    "--emit",
    type=str,
    required=False,
    default="human",
    help="Output format. One of: human, csv-overview, csv-contributions, xlsx-overview, xlsx-contributions",
)
def search(  # noqa: C901
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
    emit: str = "human",
):
    """Search summarized FEC contributions data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    searcher = ContactContributionSearcher(data_manager)

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

    def _emit_overview_csv(
        out: t.TextIO, summaries: t.Iterable[tuple[Contact, ContributionSummary]]
    ):
        """Emit a CSV overview of the search results."""
        fieldnames = [
            "last_name",
            "first_name",
            "city",
            "state",
            "zip",
            "total_usd",
            "dem_usd",
            "rep_usd",
            "other_usd",
            "donated_to",
        ]
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        for contact, summary in summaries:
            writer.writerow(
                {
                    "first_name": contact.first_name.title(),
                    "last_name": contact.last_name.title(),
                    "city": (contact.city or "").title(),
                    "state": contact.state,
                    "zip": contact.zip_code,
                    "total_usd": summary.total_cents / 100,
                    "dem_usd": summary.party_total_cents("DEM") / 100,
                    "rep_usd": summary.party_total_cents("REP") / 100,
                    "other_usd": summary.party_total_cents("OTH") / 100,
                    "donated_to": "/".join(
                        sorted(c.name for c in summary.committees())
                    ),
                }
            )

    def _emit_contributions_csv(
        out: t.TextIO, summaries: t.Iterable[tuple[Contact, ContributionSummary]]
    ):
        """Emit a detailed CSV with line-by-line transactions."""
        fieldnames = [
            "last_name",
            "first_name",
            "city",
            "state",
            "zip",
            "fec_contribution_id",
            "fec_committee_id",
            "committee",
            "party",
            "amount_usd",
        ]
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        for contact, summary in summaries:
            for contribution in summary.contributions:
                writer.writerow(
                    {
                        "first_name": contact.first_name.title(),
                        "last_name": contact.last_name.title(),
                        "city": (contact.city or "").title(),
                        "state": contact.state,
                        "zip": contact.zip_code,
                        "fec_contribution_id": contribution.id,
                        "fec_committee_id": contribution.committee_id,
                        "committee": contribution.committee.name,
                        "party": contribution.committee.party,
                        "amount_usd": contribution.amount_cents / 100,
                    }
                )

    def _emit_human(summaries: t.Iterable[tuple[Contact, ContributionSummary]]):
        for contact, summary in summaries:
            print(
                f"{contact.first_name.title()} {contact.last_name.title()} ({(contact.city or '').title()}, {contact.state})"
            )
            print(str(summary))

    def _wrap_emit(xlsx: bool, emit_fn: t.Callable):
        """Wrap an emit function to emit to XLSX."""

        def _emit(summaries: t.Iterable[t.Any]):
            if xlsx:
                csv_out = io.StringIO(newline="")
            else:
                csv_out = click.get_text_stream("stdout")
            emit_fn(csv_out, summaries)
            if xlsx:
                csv_out.seek(0)
                df = pd.read_csv(csv_out)
                # Make sure fec_contribution_id and fec_committee_id are treated as strings.
                try:
                    df["fec_contribution_id"] = df["fec_contribution_id"].astype(str)
                    df["fec_committee_id"] = df["fec_committee_id"].astype(str)
                except KeyError:
                    pass
                xlsx_out = click.get_binary_stream("stdout")
                df.to_excel(xlsx_out, index=False)

        return _emit

    summaries = searcher.search_and_summarize_contacts(contact_provider)
    sorted_summaries = sorted(
        summaries,
        key=lambda contact_summary: contact_summary[0].last_name.upper(),
    )
    if emit == "human":
        _emit_human(sorted_summaries)
    elif emit == "csv-overview" or emit == "xlsx-overview":
        _wrap_emit(emit == "xlsx-overview", _emit_overview_csv)(sorted_summaries)
    elif emit == "csv-contributions" or emit == "xlsx-contributions":
        _wrap_emit(emit == "xlsx-contributions", _emit_contributions_csv)(
            sorted_summaries
        )
    else:
        raise click.UsageError(f"Unknown emit format: {emit}")


if __name__ == "__main__":
    fec()
