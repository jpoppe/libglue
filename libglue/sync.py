"""libGlue Sync library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


from rich import print

from .shell import run_command_show_output


def rsync_backup(source: str, destination: str, excludes: list[str]):
    """Rsync wrapper."""
    command = ["sudo", "-E", "rsync", "-aAXv", "--delete", "--delete-excluded", source]
    for exclude in excludes:
        command.append("--exclude")
        command.append(exclude)
    command += ["-e", "ssh", destination]

    command_string = " ".join(command)
    print(command_string)

    run_command_show_output(command)
