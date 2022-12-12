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

    Cache = "Cache :floppy_disk:"
    Configuration = "Configuration :unicorn_face:"
    Danger = ":dragon: DANGER :fire:"
    Info = "Info :information_desk_person:"
    Lab = "Lab :test_tube:"
    Manage = "Manage :briefcase:"
    Ops = "Ops :lion:"
    Sync = "Sync :floppy_disk:"
    Test = "Test :factory:"
    View = "View :eagle:"


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
