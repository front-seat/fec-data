import pathlib
import typing as t
from decimal import Decimal

# CONSIDER: I'm using these for now, but (for instance) pydantic
# or attrs both provide pretty comprehensive tools here. (I sorta like
# the explicitness of this, though, maybe?)


class ValidationError(Exception):
    """Raised when a validation fails."""

    pass


#
# Basic type validations
#


def is_str(value: t.Any) -> bool:
    """Return True if the value is a string."""
    return isinstance(value, str)


def validate_str(value: t.Any) -> str:
    """Return the value if it is a string, otherwise raise an exception."""
    if isinstance(value, str):
        return value
    raise ValidationError(f"Expected a string, got {value}")


def is_str_or_none(value: t.Any) -> bool:
    """Return True if the value is a string or None."""
    return value is None or isinstance(value, str)


def validate_convert_decimal(value: t.Any) -> Decimal:
    """Validate a string or decimal, converting the string to a decimal."""
    try:
        return Decimal(value)
    except Exception:
        raise ValidationError(f"Expected convertible to decimal, got {value}") from None


def validate_str_or_none(value: object) -> str | None:
    """Return the value if it is a string or None, otherwise raise an exception."""
    if value is None or isinstance(value, str):
        return value
    raise ValidationError(f"Expected a string or None, got {value}")


def is_dict(value: object) -> bool:
    """Return True if the value is a dict."""
    return isinstance(value, dict)


def validate_dict(value: object) -> dict:
    """Return the value if it is a dict, otherwise raise an exception."""
    if isinstance(value, dict):
        return value
    raise ValidationError(f"Expected a dict, got {value}")


#
# Dict content validations
#


def get_str(d: dict, key: str) -> str:
    """
    Return the value for `key` in `d` if it is a string,
    otherwise raise an exception.
    """
    if key not in d:
        raise ValidationError(f"Key '{key}' not found in {d}")
    return validate_str(d[key])


def get_optional_str(d: dict, key: str) -> str | None:
    """
    Return the value for `key` in `d` if it is a string,
    otherwise raise an exception.
    """
    if key not in d:
        return None
    return validate_str(d[key])


def get_str_or_none(d: dict, key: str) -> str | None:
    """
    Return the value for `key` in `d` if it is a string or None,
    otherwise raise an exception.
    """
    if key not in d:
        raise ValidationError(f"Key '{key}' not found in {d}")
    return validate_str_or_none(d[key])


def get_convert_decimal(d: dict, key: str) -> Decimal:
    """
    Return the value for `key` in `d` if it is a string or decimal,
    otherwise raise an exception.
    """
    if key not in d:
        raise ValidationError(f"Key '{key}' not found in {d}")
    return validate_convert_decimal(d[key])


def get_dict(d: dict, key: str) -> dict:
    """
    Return the value for `key` in `d` if it is a `dict`, otherwise
    raise an exception.
    """
    if key not in d:
        raise ValidationError(f"Key '{key}' not found in {d}")
    return validate_dict(d[key])


#
# Path validations
#


def is_extant_dir(path: pathlib.Path) -> bool:
    """Return True if the path exists and is a directory."""
    path = path.resolve()
    return path.exists() and path.is_dir()


def validate_extant_dir(path: pathlib.Path) -> pathlib.Path:
    """Ensure `path` exists and is a directory."""
    path = path.resolve()
    if not path.exists():
        raise ValidationError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")
    return path


def is_extant_file(path: pathlib.Path) -> bool:
    """Return True if the path exists and is a file."""
    path = path.resolve()
    return path.exists() and path.is_file()


def validate_extant_file(path: pathlib.Path) -> pathlib.Path:
    """Ensure `path` exists and is a file."""
    path = path.resolve()
    if not path.exists():
        raise ValidationError(f"Path does not exist: {path}")
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {path}")
    return path


def is_not_extant(path: pathlib.Path) -> bool:
    """Return True if the path does not exist."""
    path = path.resolve()
    return not path.exists()


def validate_not_extant(path: pathlib.Path) -> pathlib.Path:
    """Ensure `path` does not exist."""
    path = path.resolve()
    if path.exists():
        raise ValidationError(f"Path already exists: {path}")
    return path


def validate_or_create_dir(path: pathlib.Path) -> pathlib.Path:
    """Ensure `path` exists and is a directory, creating it if necessary."""
    path = path.resolve()
    if not path.exists():
        path.mkdir(parents=True)
    elif not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")
    return path
