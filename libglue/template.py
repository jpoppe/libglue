"""libGlue template library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"

import os
import string
from pathlib import Path
from typing import Any

import jinja2

from .console import log
from .file_system import read_file, write_file


class Template:
    """Render Jinja2 template."""

    def __init__(self, template_path: Path):
        """Initialize class variables."""
        self.jinja_env = jinja2.Environment(
            extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"], loader=jinja2.FileSystemLoader(template_path)
        )

    def render(self, file_name: Path, data: Any):
        """Render jinja template."""
        template = self.jinja_env.from_string(read_file(file_name))

        try:
            return template.render(data)
        except jinja2.exceptions.UndefinedError as error:
            msg = "failed to render template: %s (data: %s) (%s)"
            log.error(msg, file_name, data, error)
            return None

    def write(self, source: Path, destination: Path, data: Any):
        """Render and write Jinja2 template."""
        content = self.render(source, data)

        if not content:
            return False

        destination.expanduser().write_text(content)
        return True


def render_template(source: Path, destination: Path, template_vars: Any, chmod: int | None = None):
    """Render template with string Template class."""
    template = string.Template(read_file(source))
    write_file(destination, template.substitute(template_vars))

    if chmod is not None:
        os.chmod(destination, int(str(chmod), 8))
