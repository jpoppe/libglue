"""
libGlue console library.

This library supplements typer and rich libraries.

References
----------
* https://rich.readthedocs.io/en/stable/console.html

"""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import getpass
import importlib.util
import logging
import os
import re
import unicodedata
from pathlib import Path
from random import randint
from typing import Any, Generator

import typer
import yaml
from _collections_abc import dict_keys
from rich import print, print_json
from rich.console import Console
from rich.highlighter import Highlighter
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import pprint
from rich.syntax import Syntax
from rich.table import Table
from rich.traceback import install
from rich.tree import Tree

from .themes import DRACULA
from .types import RenderTarget

install()

log = logging.getLogger("rich")

logConsole = Console(stderr=True)

recordConsole = Console(record=True)

logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler(console=logConsole, markup=True)]
)

console = Console()


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


def banner(text):
    """Show text banner."""
    print("")
    print(59 * "*")
    if isinstance(text, list):
        for line in text:
            print(line)
    else:
        print(text)
    print(59 * "*")
    print("")


CONSOLE_HTML_FORMAT = """\
<!DOCTYPE html>
<head>
<meta charset="UTF-8">
<style>
  {stylesheet}
  body {{ color: {foreground}; background-color: {background}; }}
  pre {{ white-space: pre-wrap; white-space: -pre-wrap; word-wrap: break-word; }}
  ::selection {{ background: #44475a; }}
</style>
</head>

<html>
<body>
  <code>
    <pre style="font-family:ui-monospace,'Fira Code',monospace">{code}</pre>
  </code>
</body>
</html>
"""


class Styles:
    """Custom styles."""

    host = "green"
    section = "bold bright_blue"
    highlight = "bold magenta"
    error = "red"
    key = "italic green"


styles = Styles()


class Links:
    """Rich links."""

    @staticmethod
    def ssh(host: str):
        """Return SSH link."""
        return f"[{styles.host}][link ssh:{host}]{host}[/link ssh:{host}][/{styles.host}]"


links = Links()


class RainbowHighlighter(Highlighter):
    """Rainbow highlighter."""

    def highlight(self, text):
        """Highlight strings."""
        for index in range(len(text)):
            text.stylize(f"color({randint(200, 220)})", index, index + 1)
            text.style = "bold"


def panel(rich_text: str):
    """Print text in panel."""
    console.print(Panel(rich_text))


def print_condensed(value: str, prefix: str | None = None):
    """
    Rich print with less new line breaks.

    Rich adds a new line character after representing a list, we strip those by setting end to ''
    and print a new line when the instance of facts[query] is not of type list.
    """
    if prefix:
        console.print(f"{prefix}", value, end="")
    else:
        console.print(value, end="")

    if not isinstance(value, list):
        print()


def load_cli_plugin(cli, entrypoint: str, *args: str):
    """Load CLI plugin."""
    if not os.path.isfile(entrypoint):
        return

    spec = importlib.util.spec_from_file_location("plugin", entrypoint)

    if spec is None:
        return

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    module.main(cli, *args)


option_render = typer.Option(RenderTarget.PRETTY.value, help="Render as.")
option_export = typer.Option(None, "--export", help="Export as HTML")


class ConsoleRender:
    """Render console data."""

    tree_list_keys = ("name", "node")

    def __init__(self, data, export: Path | None = None):
        """Initialize class variables."""
        self.console = console
        self.export = export

        if export:
            if export.suffix in (".html", ".svg"):
                self.console = Console(force_terminal=True, color_system="truecolor", record=True, width=4000)
            else:
                log.error("export only supports HTML and SVG format (invalid file extension: %s)", export.suffix)
                raise SystemExit(1)

        if isinstance(data, (Generator, dict_keys)):
            self.data = list(data)
        else:
            self.data = data

    def _export(self):
        """Export console output as HTML or SVG."""
        if self.export and self.export.suffix == ".html":
            self.console.save_html(str(self.export), theme=DRACULA, code_format=CONSOLE_HTML_FORMAT, clear=True)
            log.info("🏭 exported console output as HTML: %s", self.export)

    def _tree_from_list(self):
        """Render tree from list."""
        if all(isinstance(item, str) for item in self.data):
            log.info(":light_bulb: I don't know how to make a :palm_tree: from a list with strings")
            log.info(":innocent: I will render a table instead :tongue:")
            self.table()
            return

        tree_data = {}

        for item in self.data:
            for tree_list_key in self.tree_list_keys:
                if tree_list_key in item:
                    name = item[tree_list_key]
                    del item[tree_list_key]
                    tree_data[name] = item
                    break
            else:
                log.warning(":palm_tree: no tree list key found found in item: %s (%s)", item, self.tree_list_keys)
                log.warning(":light_bulb: if it makes sense to add a key to the `tree list keys`, please open a PR")

        if tree_data:
            self.data = tree_data

    def _stylize_key(self, key: str):
        """Stylize key."""
        return f"[bold][green]{key}[/bold][/green]:"

    def json(self):
        """Render data as JSON."""
        print_json(data=self.data)
        self._export()

    def raw(self):
        """Render raw data."""
        if isinstance(self.data, (list, tuple)):
            for item in self.data:
                print(item)
        else:
            self.json()

        self._export()

    def pretty(self):
        """Pretty print data."""
        pprint(self.data)
        self._export()

    def yaml(self):
        """Render data as YAML."""

        def default_representer(dumper, data):
            """Remove Ansible references."""
            return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))

        yaml.representer.SafeRepresenter.add_representer(None, default_representer)

        self.console.print(Syntax(yaml.safe_dump(self.data), "yaml", theme="dracula"))

        self._export()

    def _parse_tree_dict_branch(self, tree: Tree, branch_key: str, node: dict) -> None:
        """Render tree dict branch."""
        branch = tree.add(self._stylize_key(branch_key))

        for key, value in node.items():
            if isinstance(value, dict):
                self._parse_tree_branch(branch, value)
            elif isinstance(value, (dict, int, str)):
                branch.add(f"{self._stylize_key(key)} {value}")
            elif isinstance(value, list):
                sub_branch = branch.add(f"[bold][dim]{key}")
                for sub_item in value:
                    sub_branch.add(f"{sub_item}")
            else:
                log.warning("Render tree does not support branch type: %s", type(node))

    def _parse_tree_list_branch(self, tree: Tree, branch_key: str, node: list) -> None:
        """Render tree list branch."""
        if len(node) < 2:
            tree.add(f"{self._stylize_key(branch_key)} {node}")
        else:
            branch = tree.add(self._stylize_key(branch_key))
            for item in node:
                branch.add(item)

    def _parse_tree_branch(self, tree: Tree, data: Any) -> None:
        """Render tree branch."""
        for branch_key, node in data.items():
            if isinstance(node, dict):
                self._parse_tree_dict_branch(tree, branch_key, node)
            elif isinstance(node, list):
                self._parse_tree_list_branch(tree, branch_key, node)
            elif isinstance(node, (bool, str)):
                tree.add(f"{self._stylize_key(branch_key)} {node}")
            else:
                log.warning("Render tree target is compatible with `list` or `dict` not: %s", type(node))

    def tree(self):
        """Render simple tree."""
        tree = Tree(":palm_tree::evergreen_tree::tanabata_tree::christmas_tree:", guide_style="bold bright_blue")

        if isinstance(self.data, list):
            self._tree_from_list()

        if isinstance(self.data, dict):
            self._parse_tree_branch(tree, self.data)
            self.console.print(tree)
            self._export()

    def table(self):
        """Render simple table."""
        table = Table(show_header=False, expand=False)

        if isinstance(self.data, dict):
            for key, value in self.data.items():
                if isinstance(value, str):
                    table.add_row(key, value)
                else:
                    table.add_row(key, str(value))
        elif isinstance(self.data, list):
            for value in self.data:
                table.add_row(value)
        else:
            log.error("table render target supports `list` and `dict` not: %s", type(self.data))
            typer.Exit(1)

        self.console.print(table)
        self._export()


def render_raw(data: list | dict | Table | Tree | Generator[Any, None, None], path: Path):
    """Render Rich data."""
    console_render = ConsoleRender(data, path)
    console_render.raw()


def render_as(
    data: list | dict | Generator[Any, None, None],
    target: RenderTarget = RenderTarget.PRETTY,
    export: Path | None = None,
) -> None:
    """Render data to console."""
    console_render = ConsoleRender(data, export)

    if target == RenderTarget.JSON:
        console_render.json()
    elif target == RenderTarget.PRETTY:
        console_render.pretty()
    elif target == RenderTarget.RAW:
        console_render.raw()
    elif target == RenderTarget.TABLE:
        console_render.table()
    elif target == RenderTarget.TREE:
        console_render.tree()
    elif target == RenderTarget.YAML:
        console_render.yaml()
    else:
        log.error("render target unknown: %s", target)


def read_password_or_exit(type: str):
    """Read password from CLI or exit."""
    password = getpass.getpass(f"Enter {type} password: ")

    if not password:
        log.warning(":person_facepalming: {type} requires a password")
        raise SystemExit(1)

    return password
