import abc
import pathlib
import plistlib
import typing as t
import zipfile

from server.utils.validations import validate_extant_dir, validate_extant_file

from . import Contact


class ABBUManagerBase(abc.ABC):
    """
    An abstract IContactProvider (see __init__.py) that supports Apple's Address Book
    Backup format. We offer two implementations: one for a directory and one for a
    zip file.
    """

    @abc.abstractmethod
    def get_abpersons(self) -> t.Iterable[t.IO[bytes]]:
        """Return an iterator of abpersons."""
        ...

    def get_contacts(self) -> t.Iterable[Contact]:
        """Return an iterator of contacts."""
        for abperson in self.get_abpersons():
            maybe_abperson = self._parse_abperson(abperson)
            if maybe_abperson:
                yield maybe_abperson

    def _parse_abperson(self, abperson: t.IO[bytes]) -> Contact | None:
        """Parse an abperson file into a Contact."""
        try:
            plist_data = plistlib.load(abperson)
            first_name = plist_data["First"].upper()
            last_name = plist_data["Last"].upper()
            # use the preferred zip code if it exists
            try:
                address_0 = plist_data["Address"]["values"][0]
            except Exception:
                address_0 = {}
            city = address_0.get("City", "").upper() or None
            state = address_0.get("State", "").upper() or None
            if state and len(state) != 2:
                state = None

            zip_code = address_0.get("ZIP", "").replace("-", "") or None
            if zip_code and len(zip_code) not in {5, 9}:
                zip_code = None

            try:
                phone = plist_data["Phone"]["values"][0]
            except Exception:
                phone = None

        except Exception:
            return None
        return Contact(first_name, last_name, city, state, phone, zip_code)


class DirectoryABBUManager(ABBUManagerBase):
    """An ABBUManager that expects its contents to be in a local directory."""

    _path: pathlib.Path

    def __init__(self, path: str | pathlib.Path):
        """Initialize a new instance of the DirectoryABBUManager class."""
        self._path = validate_extant_dir(pathlib.Path(path))

    def get_abpersons(self) -> t.Iterable[t.IO[bytes]]:
        """Return an iterator of abpersons."""
        for path in self._path.glob("**/Sources/**/*ABPerson.abcdp"):
            yield path.open("rb")


class ZipABBUManager(ABBUManagerBase):
    """
    An IContactProvider (see __init__.py) that supports Apple's Address Book Backup
    format. We can be handed a path to an `abbu` directory *or* a path to a single
    zip file that *is* an `abbu` directory.
    """

    _path: pathlib.Path

    def __init__(self, path: str | pathlib.Path):
        """Initialize a new instance of the ZipAddressBookBackupManager class."""
        self._path = validate_extant_file(pathlib.Path(path))

    def get_abpersons(self) -> t.Iterable[t.IO[bytes]]:
        """Return an iterator of abpersons."""
        with zipfile.ZipFile(self._path) as zip_file:
            for info in zip_file.infolist():
                if (
                    info.filename.endswith("ABPerson.abcdp")
                    and "Sources" in info.filename
                    and "_MACOSX" not in info.filename
                ):
                    yield zip_file.open(info)
