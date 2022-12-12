"""libGlue CLI library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


from enum import Enum, unique

import typer

from .console import log


@unique
class DebugOption(str, Enum):
    """Debug option."""

    DEFAULT = "default"
    WAIT = "wait"


class Cli:
    """CLI related methods."""

    def __init__(self, app_name: str, version: str, debug_address: str, debug_port: int) -> None:
        """Initialize CLI options."""
        self.name = app_name
        self.version = version

        self.debug_address = debug_address
        self.debug_port = debug_port

    def version_callback(self, value: bool) -> None:
        """Return application name, version and exit."""
        if value:
            typer.echo(f"{self.name} v{self.version}")
            raise typer.Exit()

    def debug_callback(self, value: DebugOption | None) -> None:
        """Enable debugpy adapter."""
        if value:
            import debugpy

            debugpy.listen((self.debug_address, self.debug_port))
            log.info(":snake: debugpy adapter is enabled and listening on: %s:%s", self.debug_address, self.debug_port)

            if value == "wait":
                log.info(":sleeping: execution paused, waiting for debugger to attach...")
                debugpy.wait_for_client()
                log.info(":mage: debugger is now attached, continuing execution :rocket:")
