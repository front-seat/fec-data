#!/usr/bin/env python3

import json
import pathlib

import click


@click.command()
@click.argument("input", type=click.Path(exists=True, dir_okay=False))
def main(input: str):
    """
    Read a messy nicknames data file. Create a single set of unique
    matched names per line and write to stdout.
    """
    input_path = pathlib.Path(input).resolve()
    matching_names: list[set[str]] = []
    with input_path.open("rt") as input_file:
        for line in input_file:
            # Remove all commas
            line = line.replace(",", "")
            # Remove all slashes
            line = line.replace("/", "")
            # Remove parens, open and close
            line = line.replace("(", "").replace(")", "")
            # Break the line into a list of names -- split on any
            # arbitrary number of spaces
            names = line.split()
            # Remove any empty strings
            names = [stripped for name in names if (stripped := name.strip())]
            # Remove any strings that don't start with a capital letter
            names = [name for name in names if name[0].isupper()]
            # Make a set of capitalized names
            names_set = {name.upper() for name in names}
            # Print it
            matching_names.append(names_set)

    # Continuously merge sets that have overlapping names, until no
    # more merges are possible
    while True:
        index = 0
        merged = False
        while index < len(matching_names):
            index2 = index + 1
            while index2 < len(matching_names):
                if matching_names[index] & matching_names[index2]:
                    matching_names[index] |= matching_names[index2]
                    del matching_names[index2]
                    merged = True
                else:
                    index2 += 1
            index += 1
        if not merged:
            break

    name_to_index = {}
    for index, names_set in enumerate(matching_names):
        for name in names_set:
            assert name not in name_to_index
            name_to_index[name] = index

    # For each set in matching name, convert it to a sorted list
    matching_names_list = [sorted(names) for names in matching_names]

    # Reorder name_to_index so that it's alphabetical by name
    name_to_index = dict(sorted(name_to_index.items(), key=lambda x: x[0]))

    # Dump a final datastructure to stdout
    print(
        json.dumps({"names": matching_names_list, "indexes": name_to_index}, indent=2)
    )


if __name__ == "__main__":
    main()
