#!/usr/bin/env python3
# ruff: noqa: E501

import click

from server.data.fec.contributions import ContributionsManager
from server.data.manager import DataManager
from server.data.names.nicknames import MessyNicknamesManager


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
def search():
    """Search summarized FEC contributions data."""
    pass


if __name__ == "__main__":
    fec()
