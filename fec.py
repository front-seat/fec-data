#!/usr/bin/env python3
# ruff: noqa: E501

import json

import click

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
@click.argument("first_name")
@click.argument("last_name")
@click.argument("zip_code")
@click.option(
    "--data",
    type=click.Path(exists=True),
    help="Path to data dir.",
    required=False,
    default=None,
)
def search(first_name: str, last_name: str, zip_code: str, data: str | None = None):
    """Search summarized FEC contributions data."""
    data_manager = DataManager(data) if data is not None else DataManager.default()
    nicknames_manager = NicknamesManager.from_data_manager(data_manager)
    fuzzy_id = FuzzyIdentifier(
        last_name, first_name, zip_code, get_nickname_index=nicknames_manager
    ).fuzzy_id
    summaries_manager = ContributionSummariesManager.from_data_manager(data_manager)
    summary = summaries_manager.get_summary(fuzzy_id)
    if summary is None:
        print("No matching summary.")
    else:
        print(json.dumps(summary.to_data(), indent=2))


if __name__ == "__main__":
    fec()
