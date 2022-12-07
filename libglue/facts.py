"""libGlue facts library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import sys


def is_windows():
    """Return when the used operating system is Windows."""
    return True if sys.platform in ["win32", "cygwin"] else False
