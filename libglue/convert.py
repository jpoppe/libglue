"""libGlue convert library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


import humanfriendly
from dateutil import parser


def humanize_time(time: str, format: str = "%d %b, %Y %H:%M") -> str:
    """Return human readable time object."""
    return parser.parse(time).strftime(format)


def human_time(time_in_seconds: int):
    """Convert seconds to human readable units."""
    days = time_in_seconds // 86400
    hours = time_in_seconds // 3600 % 24
    minutes = time_in_seconds // 60 % 60
    seconds = time_in_seconds % 60
    return days, hours, minutes, seconds


def format_human_time(time_in_seconds: int):
    """Convert seconds to human readable time."""
    days, hours, minutes, seconds = human_time(time_in_seconds)
    return f"{days} days, {hours:02d}:{minutes:02d}:{seconds:02d}"


def convert(value, from_unit, to_unit, max_units=1):
    """Convert value between units."""
    if from_unit == to_unit:
        return value

    if from_unit == "seconds" and to_unit == "human":
        return humanfriendly.format_timespan(value, max_units=max_units)

    if from_unit == "seconds" and to_unit == "humanfriendly":
        return humanfriendly.format_timespan(int(value), max_units=max_units)

    if from_unit == "MB" and to_unit == "humanfriendly":
        size = humanfriendly.parse_size(f"{value}{from_unit}")
        return humanfriendly.format_size(size, binary=True)

    if from_unit == "bytes" and to_unit == "humanfriendly":
        return humanfriendly.format_size(int(value), binary=True)

    raise ValueError(f"conversion for `{from_unit} to {to_unit}` is not implemented")
