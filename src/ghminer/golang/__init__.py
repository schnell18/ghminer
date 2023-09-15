"""Packages for mining golang repositories on github."""

from .nameconv import (
    convert_names,
)

from .gomod import (
    grab_gomod,
)


__all__ = [
    "convert_names",
    "grab_gomod",
]
