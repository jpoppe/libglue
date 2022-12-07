"""libGlue types library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


from enum import Enum, unique
from typing import Any, Dict, List, Union

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

JSONDict = Dict[str, JSONValue]


@unique
class HelpPanel(str, Enum):
    """Help panel titles."""

    Cache = "Cache"
    Configuration = "Configuration"
    Info = "Info"
    Lab = "Lab"
    Manage = "Manage"
    Ops = "Ops"
    Sync = "Sync"
    Test = "Test"
    View = "View"


@unique
class CompressionType(str, Enum):
    """Available compression types."""

    none = None
    zip = "zip"
    sevenzip = "7zip"


@unique
class WriteFlags(str, Enum):
    """Write and append flags."""

    append = "a"
    write = "w"


@unique
class RenderTarget(str, Enum):
    """Render target."""

    JSON = "json"
    PRETTY = "pretty"
    RAW = "raw"
    TABLE = "table"
    TREE = "tree"
    YAML = "yaml"
