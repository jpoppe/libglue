"""libGlue CLI library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import typer


class Cli:
    """CLI related methods."""

    def __init__(self, app_name: str, version: str, debug_address: str, debug_port: int) -> None:
        """Initialize CLI related class variables."""
        self.name = app_name
        self.version = version
        self.debug_address = debug_address
        self.debug_port = debug_port

    def version_callback(self, value: bool) -> None:
        """Return version and exit."""
        if value:
            typer.echo(f"{self.name} v{self.version}")
            raise typer.Exit()

    def debug_callback(self, value: str) -> None:
        """Enable debugpy adapter."""
        if value:
            import debugpy

            debugpy.listen((self.debug_address, self.debug_port))
            print(f"Debugpy adapter is enabled, and listening on: {self.debug_address}:{self.debug_port}")

            if value == "wait":
                print(" - execution paused, waiting for debugger to attach...")
                debugpy.wait_for_client()
                print(" - debugger is now attached, continuing execution.")
