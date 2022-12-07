"""libGlue SSH library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import logging
from pathlib import Path
from typing import List

from paramiko.client import SSHClient
from rich import print
from scp import SCPClient

from .console import log


def initialize_ssh_connection(host: str, gateway: str | List[str] | None = None):
    """Connect via gateway."""
    if isinstance(gateway, str):
        gateway = [gateway]

    logging.basicConfig()
    logging.getLogger("paramiko").setLevel(logging.WARNING)

    ssh_client = SSHClient()
    ssh_client.load_system_host_keys()

    if gateway and isinstance(gateway, List):
        next_gateway = gateway.pop(0)
        gateway_client = initialize_ssh_connection(next_gateway, gateway)
        gateway_client.load_system_host_keys()
        gateway_socket = gateway_client.get_transport().open_channel("direct-tcpip", (host, 22), ("", 0))
    else:
        gateway_socket = None

    ssh_client.connect(hostname=host, port=22, sock=gateway_socket)
    return ssh_client


def ssh_run(ssh_client: SSHClient, command: str):
    """Run SSH command."""
    _stdin, stdout, stderr = ssh_client.exec_command(command)

    print(stdout.read().decode())
    print(stderr.read().decode())

    if ssh_client is None:
        log.warning(":person_facepalming: SSH connection failed")
        raise SystemExit(1)

    return ssh_client


def scp(ssh_client: SSHClient, source: Path, destination: Path | None = None) -> None:
    """SCP file from active SSH client."""
    ssh_client_transport = ssh_client.get_transport()

    if ssh_client_transport is None:
        log.warning(":person_facepalming: SSH transport failed")
        raise SystemExit(1)

    scp_client = SCPClient(ssh_client_transport)

    if destination is None:
        scp_client.get(str(source.expanduser()))
    else:
        scp_client.get(str(source.expanduser()), str(destination.expanduser()))
