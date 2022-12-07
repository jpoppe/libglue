"""libGlue template library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"

from pathlib import Path

import jinja2

from .console import log
from .file_system import read_file


class Template:
    """Render Jinja2 template."""

    def __init__(self, template_path):
        """Initialize class variables."""
        self.jinja_env = jinja2.Environment(
            extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"], loader=jinja2.FileSystemLoader(template_path)
        )

    def render(self, file_name, data):
        """Render jinja template."""
        template = self.jinja_env.from_string(read_file(file_name))

        try:
            return template.render(data)
        except jinja2.exceptions.UndefinedError as error:
            msg = "failed to render template: %s (data: %s) (%s)"
            log.error(msg, file_name, data, error)
            return None

    def write(self, src_file: Path, dst_file: Path, data):
        """Render and write Jinja2 template."""
        content = self.render(src_file, data)
        if not content:
            return False

        dst_file.expanduser().write_text(content)
        return True
