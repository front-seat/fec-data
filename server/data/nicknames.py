"""Tools for working with nicknames."""
import pathlib
import typing as t

from server.data.manager import DataManager
from server.utils.validations import validate_extant_file


def split_name(name: str) -> tuple[str, str]:
    """Split a name (in LAST, FIRST <MORE>) into (last, first) name."""
    name = name.strip()
    if not name:
        raise ValueError("Name is empty")

    splits = name.split(",")
    if len(splits) == 1:
        return splits[0].strip().upper(), ""

    last = splits[0].strip().upper()
    first = splits[1].strip().split(" ")[0].upper()
    return last, first


class INamesProvider(t.Protocol):
    """A protocol for getting related names."""

    def get_related_names(self, name: str) -> t.Iterable[frozenset[str]]:
        """Get the sets of related names for a given name."""
        ...


class NicknamesManager:
    """
    Tools for working with a 'messy' nicknames file.

    The presumed format of the file is a list of sets of related names. A given
    name may appear in multiple sets. The names will always start with a capital
    letter; they _may_ contain dots (`A.B.`) and apostrophes (`O'Neil`).
    """

    _related_names: tuple[frozenset[str], ...]
    """A list of sets of related names. A given name may appear in multiple sets."""

    _indexes_for_name: dict[str, frozenset[int]]
    """A dictionary mapping names to the indexes of the sets they appear in."""

    def __init__(self, names: t.Iterable[t.Iterable[str]]):
        self._related_names = tuple(
            frozenset(name.upper().strip() for name in name_set) for name_set in names
        )
        mutable_indexes_for_name = {}
        for i, name_set in enumerate(self._related_names):
            for name in name_set:
                mutable_indexes_for_name.setdefault(name, set()).add(i)

        self._indexes_for_name = {
            name: frozenset(indexes)
            for name, indexes in mutable_indexes_for_name.items()
        }

    @classmethod
    def from_nicknames(cls, text_io: t.TextIO) -> t.Self:
        """Create a manager from a file-like object."""
        return cls(frozenset(line.split(",")) for line in text_io if line.strip())

    @classmethod
    def from_path(cls, path: str | pathlib.Path) -> t.Self:
        """Create a manager from a path."""
        path = validate_extant_file(pathlib.Path(path))
        with path.open("rt") as input_file:
            return cls.from_nicknames(input_file)

    @classmethod
    def from_data_manager(cls, data_manager: DataManager) -> t.Self:
        """Create a manager from a data manager."""
        return cls.from_path(data_manager.path / "names" / "raw.txt")

    def get_related_names(self, name: str) -> t.Iterable[frozenset[str]]:
        """Get the sets of related names for a given name."""
        return frozenset(
            self._related_names[index]
            for index in self._indexes_for_name.get(name.upper().strip(), [])
        )
