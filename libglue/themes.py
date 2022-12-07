"""
libGlue themes library.

Themes are copyrighted by the original theme authors.

Theme origins:

* https://draculatheme.com
* https://github.com/catppuccin/catppuccin
"""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


from rich.terminal_theme import TerminalTheme

CATPPUCCIN_MOCHA = TerminalTheme(
    (30, 30, 46),
    (198, 208, 245),
    [
        (179, 188, 223),
        (148, 226, 213),
        (249, 226, 175),
        (135, 176, 249),
        (243, 139, 168),
        (86, 89, 112),
        (166, 227, 161),
        (245, 194, 231),
    ],
    [
        (161, 168, 201),
        (148, 226, 213),
        (249, 226, 175),
        (135, 176, 249),
        (243, 139, 168),
        (67, 70, 90),
        (166, 227, 161),
        (245, 194, 231),
    ],
)

DRACULA = TerminalTheme(
    (40, 42, 54),
    (248, 248, 242),
    [
        (40, 42, 54),
        (255, 85, 85),
        (80, 250, 123),
        (241, 250, 140),
        (189, 147, 249),
        (255, 121, 198),
        (139, 233, 253),
        (255, 255, 255),
    ],
    [
        (40, 42, 54),
        (255, 85, 85),
        (80, 250, 123),
        (241, 250, 140),
        (189, 147, 249),
        (255, 121, 198),
        (139, 233, 253),
        (255, 255, 255),
    ],
)
