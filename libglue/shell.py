"""libGlue shell library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from rich.console import Console

from .console import log

console = Console()


def run_command(
    command: str | List[str], env: Dict[str, str] | None = None, cwd: Path | None = None, skip_log: bool = False
):
    """Run shell command."""
    if isinstance(command, str):
        command = shlex.split(command)

    if not skip_log:
        log.info("running command: %s (cwd: %s, env: %s)", " ".join(command), cwd, env)

    subprocess_env = {**os.environ, **env} if env else os.environ
    return subprocess.run(
        command, cwd=cwd, env=subprocess_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )


def run_command_show_output(command: List[str], env: Dict[str, str] | None = None, cwd: Path | None = None):
    """Run shell command and show the output."""
    if isinstance(command, str):
        command = shlex.split(command)

    log.info("running command: %s (cwd: %s, env: %s)", " ".join(command), cwd, env)

    console.print()
    console.print(80 * "*")
    console.print("begin raw command output")
    console.print(80 * "*")

    subprocess_env = {**os.environ, **env} if env else os.environ

    process = subprocess.Popen(
        command, cwd=cwd, env=subprocess_env, stdout=sys.stdout, stderr=sys.stderr, encoding="utf-8", bufsize=1
    )

    process.wait()

    return_code = process.poll()

    print(return_code)

    console.print()
    console.print(80 * "*")
    console.print("end raw command output")
    console.print(80 * "*")

    # process = subprocess.Popen(command,
    #                            errors='replace',
    #                            shell=True,
    #                            stdout=subprocess.PIPE,
    #                            stderr=subprocess.PIPE)

    # while True:
    #     if not process.stdout:
    #         break

    #     realtime_output = process.stdout.readline()

    #     if realtime_output == '' and process.poll() is not None:
    #         break

    #     if realtime_output:
    #         print(realtime_output.strip(), flush=True)

    # print('running poooo....')

    # while True:
    #     if not process.stdout:
    #         break

    #     output = process.stdout.readline()
    #     if process.poll() is not None:
    #         break

    #     if output:
    #         print(output.strip())

    # if process.stderr:
    #     for line in process.stderr:
    #         sys.stderr.write(line)

    # if process.stdout:
    #     for line in process.stdout:
    #         sys.stdout.write(line)

    # while True:
    #     if not process.stdout:
    #         break

    #     line = process.stdout.readline()
    #     if not line:
    #         break

    # return subprocess.run(command, cwd=cwd, env=subprocess_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def execute(command: str):
    """Run simple string based shell command."""
    log.info(":rocket: running command: %s", command)
    subprocess.run(command, shell=True, check=False)


def run(command, shell=False, capture_output=True, text=True):
    """Execute shell command."""
    result = subprocess.run(command, shell=shell, capture_output=capture_output, text=text)
    if capture_output:
        print(result.stdout)
        print(result.stderr)
        print(f"error_code: {result.returncode}")


def shell(*args):
    """Run a local command."""
    command = " ".join(args)
    log.info("- running shell command: %s", command)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=sys.stdin)
    stdout, stderr = proc.communicate()
    return_code = proc.wait()
    if return_code:
        if stdout:
            log.info(stdout.strip())
        if stderr:
            log.error(stderr.strip())
            sys.exit(1)
    else:
        if stdout:
            return stdout.strip()
        return stdout


def shell_cd(path, *args):
    """Run a local command."""
    command = " ".join(args)
    print(f"- running shell command:\n  {command}\n")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=sys.stdin, cwd=path)
    stdout, stderr = proc.communicate()
    return_code = proc.wait()
    if return_code:
        if stdout:
            log.info(stdout.strip())
        if stderr:
            log.error(stderr.strip())
            sys.exit(1)
    else:
        if stdout:
            return stdout.strip()
        return stdout
