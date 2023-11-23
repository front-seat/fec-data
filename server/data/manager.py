import pathlib

from server.utils.validations import validate_extant_dir


class DataManager:
    """Top-level manager of all content in the data/ directory."""

    def __init__(self, path: str | pathlib.Path) -> None:
        self._path = validate_extant_dir(pathlib.Path(path))
        self._zip_code_manager = None

    @property
    def path(self) -> pathlib.Path:
        """Return the path to the data/ directory."""
        return self._path

    @classmethod
    def default(cls) -> "DataManager":
        """Return a DataManager with the default data/ directory."""
        return cls(pathlib.Path(__file__).parent.parent.parent / "data")
