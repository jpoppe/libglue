"""libGlue Sync library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


from pathlib import Path

from .shell import shell


def __build_rsync_command(
    source: Path,
    destination: str | Path,
    excludes: list[str] | None = None,
    dry: bool = False,
):
    """Construct rsync command."""
    command = ["sudo", "-E", "rsync", "-aAXv", "--delete", "--delete-excluded"]

    if dry:
        command.append("--dry-run")

    if excludes:
        for exclude in excludes:
            command.append("--exclude")
            command.append(exclude)

    command.append(f"{source}/")

    if isinstance(destination, str):
        command += ["-e", "ssh"]

    command.append(str(destination))

    return command


def rsync(
    source: Path,
    destination: str | Path,
    excludes: list[str] | None = None,
    dry: bool = False,
):
    """Rsync wrapper."""
    shell(*__build_rsync_command(source, destination, excludes, dry))
