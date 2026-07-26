"""Path formatting for anonymous analysis manifests."""

from pathlib import Path
from typing import Union


PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def package_relative(value: Union[str, Path]) -> str:
    """Return a package-relative path, or only the basename for external data."""
    path = Path(value).expanduser().resolve()
    try:
        return path.relative_to(PACKAGE_ROOT).as_posix()
    except ValueError:
        return path.name

