"""Tools for working with nicknames."""
import json
import pathlib
import typing as t

from server.data.manager import DataManager
from server.utils.validations import validate_extant_file


class MessyNicknamesManager:
    """
    Tools for working with a 'messy' nicknames file.

    The primary operation of this manager is to both clean and merge the names,
    and to provide a mapping from each name to a unique identifier.
    """

    _messy_names: list[frozenset[str]]
    """
    A list of sets of related names. A given name may appear in multiple
    sets.
    """

    _names: list[frozenset[str]] | None
    """A list of sets of related names. A given name will only appear in one set."""

    def __init__(self, messy_names: t.Sequence[frozenset[str]]):
        self._messy_names = list(messy_names)
        self._names = None

    @classmethod
    def from_messy_io(cls, io: t.TextIO) -> "MessyNicknamesManager":
        """
        Create a manager from a file-like object.

        The assumed format: on each line there is a list of related names.
        These are probably separated by spaces, although they may also be separated
        by `/` and `,` characters. There may be any number of spaces between the
        names, and there may be leading and trailing spaces. The names will always
        start with a capital letter; they _may_ contain dots (`A.B.`) and
        apostrophes (`O'Neil`). It's possible that a given name appears on multiple
        lines.
        """
        names: list[frozenset[str]] = []
        for line in io:
            # Remove all commas, slashes, parens
            line = (
                line.replace(",", "").replace("/", "").replace("(", "").replace(")", "")
            )
            # Break the line into a list of names -- split on any
            # arbitrary number of spaces
            maybe_names = line.split()
            # Remove any empty strings
            maybe_names = [
                stripped for name in maybe_names if (stripped := name.strip())
            ]
            # Remove any strings that don't start with a capital letter
            maybe_names = [name for name in maybe_names if name[0].isupper()]
            # Make a set of capitalized names
            names_set = {name.title() for name in maybe_names}
            # Add it if it's not empty
            if names_set:
                names.append(frozenset(names_set))
        return cls(names)

    @classmethod
    def from_path(cls, path: str | pathlib.Path) -> "MessyNicknamesManager":
        """Create a manager from a path."""
        path = validate_extant_file(pathlib.Path(path))
        with path.open("rt") as input_file:
            return cls.from_messy_io(input_file)

    @classmethod
    def from_data_manager(cls, data_manager: DataManager) -> "MessyNicknamesManager":
        """Create a manager from a data manager."""
        return cls.from_path(data_manager.path / "names" / "messy.txt")

    def _merge_names(self) -> None:
        """Merge the names."""
        # Continuously merge sets that have overlapping names, until no
        # more merges are possible
        names = list(self.messy_names)
        while True:
            index = 0
            merged = False
            while index < len(names):
                index2 = index + 1
                while index2 < len(names):
                    if names[index] & names[index2]:
                        names[index] |= names[index2]
                        del names[index2]
                        merged = True
                    else:
                        index2 += 1
                index += 1
            if not merged:
                break
        self._names = names

    def _merge_names_if_needed(self) -> None:
        """Merge the names if they haven't been merged yet."""
        if self._names is None:
            self._merge_names()

    @property
    def messy_names(self) -> t.Sequence[frozenset[str]]:
        """Get the list of names."""
        return self._messy_names

    @property
    def names(self) -> t.Sequence[frozenset[str]]:
        """Get the list of merged names."""
        self._merge_names_if_needed()
        assert self._names is not None
        return self._names

    @property
    def nicknames_manager(self) -> "NicknamesManager":
        """Get the nicknames manager."""
        return NicknamesManager(self.names)


class IGetNicknameIndex(t.Protocol):
    """A protocol for getting the index of a nickname."""

    def get_index(self, name: str) -> int | None:
        """Get the index of a nickname."""
        ...


class MockGetNicknameIndex(IGetNicknameIndex):
    """A simple implementation of IGetNicknameIndex useful for tests."""

    _name_to_index: dict[str, int]

    def __init__(self, names: t.Sequence[t.Iterable[str]]) -> None:
        self._name_to_index = {}
        for index, names_set in enumerate(names):
            for name in names_set:
                self._name_to_index[name] = index

    def get_index(self, name: str) -> int | None:
        """Return the index for a given nickname."""
        return self._name_to_index.get(name)


class NicknamesManager:
    """
    Tool for working with a 'clean' nicknames file.

    This is basically just the merged/indexed version of the messy nicknames
    file.
    """

    _names: list[frozenset[str]]
    """A list of sets of related names. A given name will only appear in one set."""

    _name_to_index: dict[str, int] | None = None
    """A mapping from each name to the (merged) index of the set it appears in."""

    def __init__(
        self,
        names: t.Iterable[frozenset[str]],
    ):
        self._names = list(names)
        self._name_to_index = None

    @classmethod
    def from_jsonl_io(cls, io: t.TextIO) -> "NicknamesManager":
        """
        Read from a json file and create a manager.

        The file is a json-lines file, where each line is a list of names.
        No name will appear more than once in the file.
        """
        names = (frozenset(json.loads(line)) for line in io)
        return cls(names)

    @classmethod
    def from_path(cls, path: str | pathlib.Path) -> "NicknamesManager":
        """Create a manager from a path."""
        path = validate_extant_file(pathlib.Path(path))
        with path.open("rt") as input_file:
            return cls.from_jsonl_io(input_file)

    @classmethod
    def from_data_manager(cls, data_manager: DataManager) -> "NicknamesManager":
        """Create a manager from a data manager."""
        return cls.from_path(data_manager.path / "names" / "nicknames.json")

    def to_data_lines(self) -> t.Iterable[list[str]]:
        """Convert to a json-serializable object."""
        return (list(names) for names in self.names)

    def to_jsonl_io(self, io: t.TextIO) -> None:
        """Write to a json file."""
        for data_line in self.to_data_lines():
            io.write(json.dumps(data_line))
            io.write("\n")

    def to_jsonl_path(self, path: str | pathlib.Path) -> None:
        """Write to a json file."""
        path = pathlib.Path(path)
        with path.open("wt") as output_file:
            self.to_jsonl_io(output_file)

    def to_jsonl_data_manager(self, data_manager: DataManager) -> None:
        """Write to a json file."""
        self.to_jsonl_path(data_manager.path / "names" / "nicknames.json")

    def _index_names(self) -> None:
        """Index the merged names."""
        self._name_to_index = {}
        for index, names_set in enumerate(self.names):
            for name in names_set:
                if name in self._name_to_index:
                    raise ValueError(f"Name {name} appears in multiple sets")
                self._name_to_index[name] = index

    def _index_names_if_needed(self) -> None:
        """Index the merged names if they haven't been indexed yet."""
        if self._name_to_index is None:
            self._index_names()

    @property
    def names(self) -> t.Sequence[frozenset[str]]:
        """Get the list of merged names."""
        return self._names

    @property
    def name_to_index(self) -> t.Mapping[str, int]:
        """Get the mapping from name to index."""
        self._index_names_if_needed()
        assert self._name_to_index is not None
        return self._name_to_index

    def get_index(self, name: str) -> int | None:
        """Get the index of a name."""
        return self.name_to_index.get(name.title())

    def get_names_for_index(self, index: int) -> frozenset[str]:
        """Get the names associated with an index."""
        if index < 0 or index >= len(self._names):
            return frozenset()
        return self.names[index]

    def get_related_names(self, name: str) -> frozenset[str]:
        """
        Get the set of related names for a name.

        The set will include the name itself.
        """
        index = self.get_index(name)
        if index is None:
            return frozenset()
        return self.get_names_for_index(index)
