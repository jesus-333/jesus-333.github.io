"""Date normalisation.

One canonical form in cv.toml -- a quoted string -- and three different
shapes on the way out. The granularity of the input is preserved: "2023"
and "2023-01" are different statements and must not be conflated.
"""

import calendar
import datetime as _dt
import re

from .errors import CvError

PRESENT = "present"

_YEAR = re.compile(r"^\d{4}$")
_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_DAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def parse(value, field):
    """Return (kind, y, m, d). kind is 'year' | 'month' | 'day' | 'present' | 'empty'."""
    if value is None or value == "":
        return ("empty", 0, 0, 0)
    if isinstance(value, (_dt.date, _dt.datetime)):
        raise CvError(
            f"{field}: dates must be quoted strings in cv.toml, got a TOML date "
            f"literal ({value!r}). Write it as \"{value.year:04d}-{value.month:02d}\" "
            f"-- an unquoted date silently becomes day granularity."
        )
    if not isinstance(value, str):
        raise CvError(f"{field}: expected a date string, got {type(value).__name__}")
    v = value.strip()
    if v == PRESENT:
        return ("present", 0, 0, 0)
    if _YEAR.match(v):
        return ("year", int(v), 0, 0)
    m = _MONTH.match(v)
    if m:
        mm = int(m.group(2))
        if not 1 <= mm <= 12:
            raise CvError(f"{field}: month out of range in {value!r}")
        return ("month", int(m.group(1)), mm, 0)
    m = _DAY.match(v)
    if m:
        return ("day", int(m.group(1)), int(m.group(2)), int(m.group(3)))
    raise CvError(
        f'{field}: unrecognised date {value!r}. Use "YYYY", "YYYY-MM", '
        f'"YYYY-MM-DD" or "present".'
    )


def to_rendercv(value, field):
    """rendercv accepts partial dates and the bare word `present`."""
    kind, y, m, _ = parse(value, field)
    if kind == "empty":
        return None
    if kind == "present":
        return PRESENT
    if kind == "year":
        return y  # an int, matching the shipped template's `start_date: 1900`
    return value


def to_jsonresume(value, field, *, end=False):
    """JSON Resume wants a full YYYY-MM-DD, or no key at all for ongoing.

    A start pads to the first instant of its period and an end to the last:
    padding an end of "2024" to 2024-01-01 would make the range look shorter
    than it is to anything that computes durations.
    """
    kind, y, m, d = parse(value, field)
    if kind in ("empty", "present"):
        return None
    if kind == "year":
        return f"{y}-12-31" if end else f"{y}-01-01"
    if kind == "month":
        last = calendar.monthrange(y, m)[1]
        return f"{y}-{m:02d}-{last:02d}" if end else f"{y}-{m:02d}-01"
    return f"{y}-{m:02d}-{d:02d}"


def to_tex(value, field):
    """LaTeX shows MM/YYYY, or a bare year when that is all we know."""
    kind, y, m, _ = parse(value, field)
    if kind == "empty":
        return ""
    if kind == "present":
        return PRESENT
    if kind == "year":
        return str(y)
    return f"{m:02d}/{y}"


def tex_range(start, end, field):
    """`01/2022 -- 01/2025`.

    An empty end renders as `01/2022 --` and is NOT silently promoted to
    "present": an accidentally blank end date should look wrong, not turn
    a finished job into a current one.
    """
    return f"{to_tex(start, field + '.start')} -- {to_tex(end, field + '.end')}".rstrip()


def sort_key(value, field, *, end=False):
    """Reverse-chronological ordering. `present` sorts last."""
    kind, y, m, d = parse(value, field)
    if kind == "present":
        return (9999, 12, 31)
    if kind == "empty":
        return (0, 0, 0)
    if kind == "year":
        return (y, 12, 31) if end else (y, 1, 1)
    if kind == "month":
        return (y, m, calendar.monthrange(y, m)[1] if end else 1)
    return (y, m, d)
