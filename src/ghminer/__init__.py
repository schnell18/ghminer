"""Packages for github mining."""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ghminer")
except PackageNotFoundError:
    __version__ = "unknown version"
