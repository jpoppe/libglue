"""libGlue shell library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import subprocess
import sys

from .console import log


def shell(*args, **kwargs):
    """Run a local command."""
    log.info(":computer: %s", " ".join(args))

    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=sys.stdin, **kwargs) as process:
        stdout, stderr = process.communicate()
        return_code = process.wait()

        if return_code:
            if stdout:
                log.info(stdout.strip())
                return stdout

            if stderr:
                log.error(stderr.strip())
                raise SystemError(1)

        if stdout:
            return stdout.strip()

        return stderr
