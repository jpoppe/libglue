"""libGlue data library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"

import difflib
import hashlib
import json
import re
import unicodedata
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List
from xml.etree import ElementTree

import yaml

from .console import log
from .shell import shell


class Struct:
    """Dict to class."""

    def __init__(self, **entries: Any):
        """Load dictionary as class."""
        self.__dict__.update(entries)

    def get(self, _key: str):
        """Get class property."""
        return self.__dict__.get(_key)


class ExplicitDumper(yaml.SafeDumper):  # pylint: disable=too-many-ancestors
    """YAML dumper that will never emit aliases."""

    def ignore_aliases(self, _data):
        """Ignore anchors."""
        return True


class IndentAllDumper(yaml.Dumper):
    """Custom YAML dumper which indents all elements for improved readability."""

    @abstractmethod
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        """Override the increase_indent method."""
        super().increase_indent(flow, False)  # type: ignore


def yprint(obj):
    """Print objects as YAML."""
    print(yaml.dump(obj, default_flow_style=False, Dumper=ExplicitDumper).strip())


def load_command_json(command: List[str], env: Dict[str, str] | None = None, cwd: Path | None = None):
    """Run command with JSON lines, return lines as dictionary."""
    return load_json(shell(*command, env, cwd))


def sort_dictionary(dictionary: Dict[Path, Any]):
    """Sort Python dictionary by key."""
    return dict(sorted(dictionary.items(), key=lambda item: item[0]))


def sort_dictionary_by_value(dictionary: Dict[str, Any]):
    """Sort Python dictionary by value."""
    return sorted(dictionary.items(), key=lambda item: (item[1], item[0]))


def sort_list_by_dictionary_value(items: list[Dict[str, Any]], key: str):
    """Sort Python list with dictionaries by dictionary value."""
    return sorted(items, key=lambda dictionary: dictionary[key])


def dump_yaml(data: dict[Any, Any], explicit_start: bool = True):
    """Dump Python object as YAML."""
    return yaml.dump(
        data,
        default_flow_style=False,
        indent=2,
        sort_keys=False,
        explicit_start=explicit_start,
        Dumper=IndentAllDumper,
    )


def load_json(json_data: str):
    """Load JSON and return Python dictionary."""
    try:
        return json.loads(json_data)
    except (ValueError, TypeError) as error:
        log.error("JSON data: %s", json_data)
        log.error("failed to load JSON string (%s)", error)
        raise SystemExit(1) from error


def reindent(string: str, number_of_spaces: int):
    """Remove leading spaces from string."""
    split: List[str] = string.split("\n")
    split = [(number_of_spaces * " ") + line.lstrip() for line in split]
    return "\n".join(split)


def hash_string(text: str):
    """Convert string to MD5 hash."""
    return hashlib.md5(text.encode()).hexdigest()


def path_list_to_dict(data: Dict) -> Dict:
    """Transform list to nested dict."""
    for path in list(data):
        working_dict = data

        value = data.pop(path)

        *folders, subpath = path.strip("/").split("/")

        for folder in folders:
            sub_dict = working_dict.setdefault(folder, {})
            if not isinstance(sub_dict, dict):
                raise ValueError("Inconsistent values detected")
            working_dict = sub_dict

        if subpath in working_dict:
            raise ValueError("Inconsistent values detected")
        working_dict[subpath] = value
    return data


def load_xml_file(path: Path):
    """Return XML root."""
    return ElementTree.parse(path)


def write_xml(path: Path, root_element):
    """Write XML tree to file."""
    log.debug("writing XML file: %s", path)
    tree = ElementTree.ElementTree(root_element)
    ElementTree.indent(tree, space=2 * " ", level=0)
    tree.write(path, xml_declaration=True, encoding="utf-8")


def diff(before: str | Any, after: str | Any):
    """Return colored visual diff report."""
    lines: List[str] = []

    def append(data: Any, style: str | None = None):
        """Append to lines."""
        if style:
            if "\n" in data:
                for line in data.split("\n"):
                    lines.append(f"[{style}]{line}[/{style}]\n")
            else:
                lines.append(f"[{style}]{data}[/{style}]")
        else:
            lines.append(data)

    if not isinstance(before, str):
        before = json.dumps(before)

    if not isinstance(after, str):
        after = json.dumps(after)

    matcher = difflib.SequenceMatcher(None, before, after)
    for opcode, after_0, after_1, before_0, before_1 in matcher.get_opcodes():
        if opcode == "equal":
            append(before[after_0:after_1])
        elif opcode == "insert":
            append(after[before_0:before_1], "green")
        elif opcode == "delete":
            append(before[after_0:after_1], "bright_white on red")
        elif opcode == "replace":
            append(after[before_0:before_1], "bright_white on green")
            append(before[after_0:after_1], "bright_white on red")

    return "".join(lines)


def query(data: Dict[Any, Any], current_query: str, full_query: str | None = None):
    """Return value for given query string."""
    full_query = full_query if full_query else current_query

    if "." not in current_query or current_query in data:
        try:
            result = data[current_query]
        except KeyError:
            return None

        return str(result) if isinstance(result, (int, list)) else result

    key, remaining_query = current_query.split(".", 1)

    try:
        if key.endswith("[]"):
            lookup_key, nested_key = full_query.rsplit("[].", 1)
            values = [
                nested_fact_value
                for data in data[lookup_key]
                for nested_fact_key, nested_fact_value in data.items()
                if nested_fact_key == nested_key
            ]
            return str(values)

    except KeyError as error:
        log.warning("could not lookup: %s", error)
        return ""

    if key in data:
        return query(data[key], remaining_query, full_query)

    # handle key names with a dot
    partial_key, remaining_query = remaining_query.split(".", 1)
    return query(data[f"{key}.{partial_key}"], remaining_query, full_query)


def diff_string(old, new):
    """Return colored visual diff report."""
    from wasabi import color

    def green_background(value):
        return color(value, fg=16, bg="green")

    def red_background(value):
        return color(value, fg=16, bg="red")

    output = []
    matcher = difflib.SequenceMatcher(None, old, new)
    for opcode, i_0, i_1, j_0, j_1 in matcher.get_opcodes():
        if opcode == "equal":
            output.append(old[i_0:i_1])
        elif opcode == "insert":
            output.append(green_background(new[j_0:j_1]))
        elif opcode == "delete":
            output.append(red_background(old[i_0:i_1]))
        elif opcode == "replace":
            output.append(red_background(old[i_0:i_1]))
            output.append(green_background(new[j_0:j_1]))
    return "".join(output)


def slugify(value, allow_unicode=False):
    """
    Slugify.

    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
