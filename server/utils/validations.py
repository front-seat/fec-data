import pathlib


class ValidationError(Exception):
    """Raised when a validation fails."""

    pass


def is_str(value: object) -> bool:
    """Return True if the value is a string."""
    return isinstance(value, str)


def validate_str(value: object) -> str:
    """Return the value if it is a string, otherwise raise an exception."""
    if isinstance(value, str):
        return value
    raise ValidationError(f"Expected a string, got {value}")


def is_str_or_none(value: object) -> bool:
    """Return True if the value is a string or None."""
    return value is None or isinstance(value, str)


def validate_str_or_none(value: object) -> str | None:
    """Return the value if it is a string or None, otherwise raise an exception."""
    if value is None or isinstance(value, str):
        return value
    raise ValidationError(f"Expected a string or None, got {value}")


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
