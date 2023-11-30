#!/usr/bin/env python3
# ruff: noqa: E501
import typing as t

import click
import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm


def _get(npa_id: str) -> str:
    result = httpx.post(
        "https://nationalnanpa.com/enas/displayNpaCityReport.do", data={"npaId": npa_id}
    )
    result.raise_for_status()
    return result.text


def _table(npa_id: str):
    html = _get(npa_id)
    soup = BeautifulSoup(html, "html.parser")
    return soup.find_all("table", attrs={"border": "1"})[0]


def _rows(npa_id: str):
    return _table(npa_id).find_all("tr", attrs={"align": "CENTER"})[1:]


def _tuples(npa_id: str) -> t.Iterable[tuple[str, str, str]]:
    for row in _rows(npa_id):
        cells = row.find_all("td")
        yield (cells[0].text.strip(), cells[1].text.strip(), cells[3].text.strip())


def _npa_ids() -> t.Iterable[str]:
    with open("data/npa/npa_ids.txt") as f:
        for line in f:
            yield line.strip()


@click.command()
def download_area_codes():
    """Download details about area codes (aka npa_ids) from NAMPA."""
    all_tuples = []
    npa_ids = list(_npa_ids())
    for npa_id in tqdm(npa_ids):
        all_tuples.extend(_tuples(npa_id))

    with open("data/npa/npa_details.csv", "w") as f:
        f.write("area_code,city,state\n")
        for area_code, city, state in all_tuples:
            f.write(f"{area_code},{city},{state}\n")


if __name__ == "__main__":
    download_area_codes()
