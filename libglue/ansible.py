"""
libGlue Ansible library.

Ansible order of precedence from least to greatest (the last listed variables override all other variables):

  * command line values (for example, -u my_user, these are not variables)

  * role defaults (defined in role/defaults/main.yml)

  * inventory file or script group vars
    inventory group_vars/all
    playbook group_vars/all
    inventory group_vars/*
    playbook group_vars/*

  * inventory file or script host vars
    inventory host_vars/*
    playbook host_vars/*
    host facts / cached set_facts

  * play vars
    play vars_prompt
    play vars_files
    role vars (defined in role/vars/main.yml)
    block vars (only for tasks in block)
    task vars (only for the task)
    include_vars
    set_facts / registered vars
    role (and include_role) params
    include params

  * extra vars (for example, -e "user=my_user") will always win precedence

(Unused) Ansible InventoryManager methods:
  add_dynamic_group
  add_dynamic_host
  add_group
  add_host
  clear_caches
  clear_pattern_cache
  get_groups_dict
  get_host
  get_hosts
  groups
  hosts
  list_groups
  list_hosts
  localhost
  parse_source
  parse_sources
  reconcile_inventory
  refresh_inventory
  remove_restriction
  restrict_to_hosts
  subset
"""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import os
import sys
from enum import Enum
from pathlib import Path

import typer
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from rich.table import Table

from .console import log
from .convert import convert
from .data import query
from .file_system import create_directory, load_json_directory_with_age, load_json_file_with_age
from .shell import execute

app_name = sys.argv[0].rsplit("/", maxsplit=1)[-1]


def _check_ansible_response(response, show_log=True):
    """Return False when there are issues found in Ansible JSON result."""
    if "failed" in response and response["failed"] or "unreachable" in response and response["unreachable"]:
        if show_log:
            log.warning("failed retrieve requested data with Ansible: %s", response["msg"])
        return False

    return True


def _get_inventory_path(name: str | None, directory: Path):
    """Return inventory file."""
    if not name:
        return None

    inventory_file = directory / f"{name}.yaml"
    if not inventory_file.exists():
        log.critical("inventory file not found: %s", inventory_file)
        sys.exit(1)

    return inventory_file


def _get_inventory_files(inventories_directory: Path, sources: str | Path | Enum | list[str | Path | Enum]):
    """Convert sources to a list with str paths for Ansible InventoryManagerService."""
    if not inventories_directory.is_dir():
        create_directory(inventories_directory)

    if not isinstance(sources, list):
        sources = [sources]

    ansible_sources = []

    for source in sources:
        if isinstance(source, Enum):
            source = source.value

        if isinstance(source, str) and source == "all":
            return [str(path) for path in inventories_directory.iterdir()]

        if isinstance(source, str):
            if source.rstrip("/") == str(inventories_directory).rstrip("/"):
                pass
            else:
                source = str(_get_inventory_path(source, inventories_directory))

        ansible_sources.append(str(source))

    return ansible_sources


class FactsViewer:
    """View facts."""

    excludes: list[str] = []
    includes: list[str] = []

    def __init__(self, views, directory: Path, inventories_directory: Path, cache_directory: Path):
        """Initialize facts manager."""
        self.directory = directory
        self.cache_directory = cache_directory
        self.inventories_directory = inventories_directory
        self.views = views

        if not self.directory.is_dir():
            log.warning(":person_facepalming: facts cache directory is empty: %s", directory)
            log.info(":light_bulb: try to run `%s inventory collect ...`", app_name)
            raise SystemExit(1)

    def _human_readable_fact_value(self, value, unit=None):
        """Make fact value human readable."""
        return convert(value, unit, "humanfriendly") if unit else value

    def _columns(self, view, row):
        """Process facts according view."""
        columns = [f'[green]{row["ansible_fqdn"]}', row["age"]]

        for item in view:
            value = query(row, item["key"])
            if "unit" in item:
                columns.append(self._human_readable_fact_value(value, item["unit"]))
            else:
                columns.append(value)

        return columns

    def _table(self, view, rows):
        """Create facts table."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Host")
        table.add_column("Age")

        for item in view:
            table.add_column(item["description"])

        for row in rows:
            if "unreachable" in row:
                table.add_row(f'[red]{row["hostname"]}', row["age"])
            else:
                columns = self._columns(view, row)
                table.add_row(*columns)

        return table

    def tree(self, host, facts, inventory_tree, view):
        """Create host tree."""
        color = "red" if "unreachable" in facts else "green"
        host_branch = inventory_tree.add(f":globe_with_meridians: [{color}]{host.stem}[/{color}] [dim]{facts['age']}")
        docker_cache_file = self.cache_directory / "docker" / f"{host.name}.json"

        if docker_cache_file.is_file():
            docker_cache = load_json_file_with_age(docker_cache_file)
            for container in docker_cache["containers"]:
                if len(container["Names"]) > 1:
                    log.warning("more then one container name found: %s", container["Names"])

                container_branch = host_branch.add(f'{container["Names"][0]} {container["Created"]}')

                for mount in container["Mounts"]:
                    if mount["Source"]:
                        container_branch.add(f':file_folder: {mount["Source"]}')
                    else:
                        container_branch.add(f":file_folder: {mount}")
                # print(container.keys())
                for port in container["Ports"]:
                    container_branch.add(str(port))
                    # for port_key, port_value in port.items():
                    #     container_branch.add(f"{port_key}: {port_value}")

        for view_cfg in self.views[view.value]:
            try:
                value = query(facts, view_cfg["key"])
                if value:
                    value = self._human_readable_fact_value(value, view_cfg.get("unit"))
                    host_branch.add(f'[bold][dim]{view_cfg["description"]}[/dim][/bold]: {value}')
            except ValueError:
                log.debug("could not find value: %s", view_cfg["key"])

    def table(self, view):
        """Build and return Rich table."""
        facts_manager = FactsManager(self.directory, self.inventories_directory)
        facts = facts_manager.load_directory(include=self.includes, exclude=self.excludes).values()
        return self._table(self.views[view.value], facts)


class FactsManager:
    """Manage facts."""

    def __init__(self, directory: Path, inventories_directory: Path):
        """Initialize facts manager."""
        self.directory = directory
        self.inventories_directory = inventories_directory

    def load_directory(self, include: list[str] | None = None, exclude: list[str] | None = None):
        """Read facts from directory as Python dictionary."""
        facts = {}

        for host, data in load_json_directory_with_age(self.directory).items():
            if not _check_ansible_response(data, False):
                facts[host] = {**data, "hostname": host.name, "age": data["age"]}
            elif "ansible_facts" in data:
                facts[host] = {**data["ansible_facts"], "age": data["age"]}

        if include:
            facts = {host.name: fact for host, fact in facts.items() if host.name in include}

        if exclude:
            facts = {host_name: fact for host_name, fact in facts.items() if host_name not in exclude}

        return facts

    def load_host(self, host: str):
        """Read host facts."""
        facts_file = self.directory / host
        if not os.path.isfile(facts_file):
            log.warning("no collected found for host: %s", host)
            return {}

        facts = load_json_file_with_age(facts_file)

        if not _check_ansible_response(facts, False):
            return {**facts, "hostname": host, "age": facts["age"]}

        if "ansible_facts" in facts:
            return {**facts["ansible_facts"], "age": facts["age"]}

        return facts

    def get_view(self, facts, view):
        """Process given facts as described in fact view."""
        result = {}

        if not _check_ansible_response(facts, False):
            log.warning("failed to retrieve facts: %s", facts["msg"])
            return result

        for item in view:
            value = query(facts, item["key"])
            human_readable_value = convert(value, item["unit"], "humanfriendly") if "unit" in item else value
            result[item["description"]] = human_readable_value

        return result

    def collect(self, inventories: str | Path | Enum | list[str | Path | Enum], target: str):
        """Collect facts."""
        for inventory_file in _get_inventory_files(self.inventories_directory, inventories):
            ansible_command = f"ansible --inventory {inventory_file}"
            ansible_command += f" --module-name gather_facts --tree '{self.directory}' {target}"
            execute(ansible_command)
            # ansible_command += f" --module-name gather_facts --tree '{facts_directory / inventory_name}' {target}"


class Ansible:
    """Glue Ansible wrapper."""

    _sources: list[str] = []

    def __init__(self, inventories_directory: Path, sources: str | Path | Enum | list[str | Path | Enum] = "all"):
        """Initialize service."""
        loader = DataLoader()
        self._sources = _get_inventory_files(inventories_directory, sources)
        self._inventory = InventoryManager(loader=loader, sources=self._sources)
        self._variable_manager = VariableManager(loader=loader, inventory=self._inventory)

    @property
    def groups(self):
        """Return inventory groups."""
        return list(self._inventory.groups)

    @property
    def hosts(self):
        """Return inventory hosts."""
        return list(self._inventory.hosts)

    def get_groups(self, group: str):
        """Return groups from group."""
        groups = self._inventory.get_groups_dict()

        if not groups:
            return []

        return groups.get(group, [])

    def play(self, playbook: Path, limit: str, check: bool = True, std_out_callback: str | None = None):
        """Run playbook."""
        for inventory_file in self._sources:
            ansible_command = ""
            if std_out_callback:
                ansible_command += f"ANSIBLE_STDOUT_CALLBACK={std_out_callback} "
            ansible_command += f"ansible-playbook --inventory {inventory_file} --limit {limit} --diff {playbook}"
            ansible_command += " --ask-become-pass --become-method sudo"
            if check:
                ansible_command += " --check"
            execute(ansible_command)


class AnsibleCompletion:
    """Ansible completion class."""

    def __init__(self, inventories_directory: Path):
        """Set path."""
        self.inventories_directory = inventories_directory

    def complete_argument_inventory_group(self, ctx: typer.Context):
        """Inventory group completion."""
        return Ansible(self.inventories_directory, ctx.params.get("inventory", "all")).groups

    def complete_argument_inventory_host(self, ctx: typer.Context):
        """Inventory host completion."""
        inventory_name = ctx.params.get("inventory")

        if not inventory_name:
            return []

        return Ansible(self.inventories_directory, inventory_name).hosts

    def complete_argument_inventory_target(self, ctx: typer.Context):
        """Inventory target (host or group) completion."""
        inventory_name = ctx.params.get("inventory")
        if not inventory_name:
            return []

        ansible = Ansible(self.inventories_directory, inventory_name)
        return ansible.hosts + ansible.groups
