"""libGlue facts library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import sys
from pathlib import Path


def is_windows() -> bool:
    """Return True when operating system is Windows."""
    return sys.platform in ["win32", "cygwin"]


def is_systemd() -> bool:
    """Return True when operating system is based on systemd (Requires root rights)."""
    return "systemd" in str(Path("/proc/1/exe").readlink())
