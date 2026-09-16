"""Turning plain strings into safe LaTeX.

Two passes, in this order:

  1. escape()      the ten characters LaTeX treats as special
  2. typography()  Unicode punctuation that has a nicer LaTeX spelling

The escaping is a SINGLE regex substitution, never chained str.replace:
escaping the backslash first and the braces second would corrupt the
braces that step one just introduced.

Accented Latin (Joao -> Jo{\~a}o, Universita) is deliberately left as
UTF-8. zancanarocv.sty loads inputenc/utf8 and fontenc/T1, which handle
it correctly; transliterating would be wrong, not safer.
"""

import re

from .errors import CvError

_MAP = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_RE = re.compile("|".join(re.escape(k) for k in sorted(_MAP, key=len, reverse=True)))

_TYPO = [
    ("—", "---"),
    ("–", "--"),
    ("…", r"\ldots{}"),
    ("“", "``"),
    ("”", "''"),
    ("‘", "`"),
    ("’", "'"),
    ("→", r"$\rightarrow$"),
]

_TODO = re.compile(r"@TODO\{([^{}]*)\}")

# RFC 3986 characters, plus nothing else. Anything outside this set in a
# URL is a mistake we want to hear about at generate time.
_URL_OK = re.compile(r"^[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+$")


def escape(text):
    if text is None:
        return ""
    out = _RE.sub(lambda m: _MAP[m.group()], str(text))
    for src, dst in _TYPO:
        out = out.replace(src, dst)
    return out


def has_todo(text):
    return bool(_TODO.search(str(text or "")))


def strip_todo(text):
    """Website form: drop the marker, keep the words inside it."""
    return _TODO.sub(r"\1", str(text or ""))


def tex_todo(text):
    """LaTeX form: escape the contents, then wrap them in \\cvTODO{}.

    Run BEFORE escape() on the surrounding string -- the marker's braces
    are ours, not the user's, and must survive escaping.
    """
    parts, last = [], 0
    for m in _TODO.finditer(str(text or "")):
        parts.append(escape(text[last : m.start()]))
        parts.append(r"\cvTODO{" + escape(m.group(1)) + "}")
        last = m.end()
    parts.append(escape(text[last:]))
    return "".join(parts)


def verbatim_check(text, field):
    """Validate a `_tex` opt-out field before trusting it verbatim."""
    s = str(text or "")
    if s.count("{") != s.count("}"):
        raise CvError(f"{field}: unbalanced braces in a _tex field: {s!r}")
    if re.search(r"(?<!\\)\\$", s):
        raise CvError(f"{field}: _tex field ends in a dangling backslash: {s!r}")
    return s


def url(value, field):
    """URLs get their own, much narrower escaping.

    Text-escaping a URL would break percent-encoding, so only # and %
    are escaped -- the two characters hyperref cannot read raw.
    """
    if not value:
        return ""
    s = str(value).strip()
    if re.search(r"[{}\\\s]", s):
        raise CvError(
            f"{field}: URL contains a brace, backslash or whitespace: {s!r}. "
            f"hyperref cannot take that; percent-encode it."
        )
    if not _URL_OK.match(s):
        raise CvError(f"{field}: URL has characters outside RFC 3986: {s!r}")
    return s.replace("#", r"\#").replace("%", r"\%")


def href(target, label, field):
    """\\href{url}{label}, or the bare label when there is no target."""
    if not target:
        return label
    return r"\href{" + url(target, field) + "}{" + label + "}"
