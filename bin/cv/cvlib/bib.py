"""A small, brace-aware BibTeX reader.

Deliberately dependency-free. The alternative (bibtexparser) is a fine
library, but this file has one well-controlled producer -- exports from
publishers and Scholar -- and a ~150-line reader keeps `make cv-check`
runnable anywhere Python is, including a bare CI container.

THE SHARP EDGE IN THIS MODULE: BibTeX field values are already LaTeX.
Going to .tex they pass through VERBATIM and must not be escaped. Going
to the website they must be decoded to Unicode first. Both directions
are wrong if you use the other one's rule.
"""

import re

from .errors import CvError

# LaTeX accent spellings that actually occur in bibliographies. Not
# exhaustive by design: an unknown one is reported, not silently mangled.
_ACCENTS = {
    ("~", "a"): "\u00e3", ("~", "n"): "\u00f1", ("~", "o"): "\u00f5",
    ("'", "a"): "\u00e1", ("'", "e"): "\u00e9", ("'", "i"): "\u00ed",
    ("'", "o"): "\u00f3", ("'", "u"): "\u00fa", ("'", "c"): "\u0107",
    ("'", "s"): "\u015b", ("'", "n"): "\u0144", ("'", "z"): "\u017a",
    ("`", "a"): "\u00e0", ("`", "e"): "\u00e8", ("`", "i"): "\u00ec",
    ("`", "o"): "\u00f2", ("`", "u"): "\u00f9",
    ('"', "a"): "\u00e4", ('"', "e"): "\u00eb", ('"', "i"): "\u00ef",
    ('"', "o"): "\u00f6", ('"', "u"): "\u00fc",
    ("^", "a"): "\u00e2", ("^", "e"): "\u00ea", ("^", "i"): "\u00ee",
    ("^", "o"): "\u00f4", ("^", "u"): "\u00fb",
    ("c", "c"): "\u00e7", ("c", "s"): "\u015f",
    ("v", "c"): "\u010d", ("v", "s"): "\u0161", ("v", "z"): "\u017e",
    ("v", "r"): "\u0159", ("v", "e"): "\u011b",
    ("H", "o"): "\u0151", ("u", "a"): "\u0103", ("u", "g"): "\u011f",
    ("=", "a"): "\u0101", ("=", "e"): "\u0113", (".", "z"): "\u017c",
}
_SPECIALS = {r"\ss": "\u00df", r"\o": "\u00f8", r"\O": "\u00d8",
             r"\aa": "\u00e5", r"\l": "\u0142", r"\L": "\u0141",
             r"\ae": "\u00e6", r"\&": "&", r"\%": "%", r"\_": "_",
             r"\#": "#", r"\$": "$", r"---": "\u2014", r"--": "\u2013"}


def to_unicode(value):
    """Decode the LaTeX-isms a .bib carries, for the web outputs."""
    s = value
    # {\~a} / \~{a} / \'e ... in the three spellings that occur in practice
    s = re.sub(r"\{\\(.)\{?(\w)\}?\}", lambda m: _ACCENTS.get((m.group(1), m.group(2)),
                                                             m.group(0)), s)
    s = re.sub(r"\\(.)\{(\w)\}", lambda m: _ACCENTS.get((m.group(1), m.group(2)),
                                                        m.group(0)), s)
    for src, dst in _SPECIALS.items():
        s = s.replace(src, dst)
    # Brace groups in BibTeX only protect capitalisation; drop them.
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def _split_fields(body):
    """Split `a = {..}, b = {..}` respecting brace nesting and quotes."""
    fields, depth, buf = {}, 0, []
    for ch in body:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if ch == "," and depth == 0:
            _store(fields, "".join(buf))
            buf = []
        else:
            buf.append(ch)
    _store(fields, "".join(buf))
    return fields


def _store(fields, chunk):
    if "=" not in chunk:
        return
    key, _, val = chunk.partition("=")
    key = key.strip().lower()
    val = val.strip()
    if val.startswith("{") and val.endswith("}"):
        val = val[1:-1]
    elif val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    if key:
        fields[key] = re.sub(r"\s+", " ", val).strip()


def parse(path):
    """Return a list of {key, type, fields}. Errors on a duplicate key."""
    text = open(path, encoding="utf-8").read()
    # Tolerate (and ignore) a jekyll-scholar YAML front-matter fence.
    if text.lstrip().startswith("---"):
        text = text.lstrip().split("---", 2)[2]

    entries, seen = [], {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        start = m.end()
        depth, i = 1, m.start(0) + text[m.start(0):].index("{")
        i += 1
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start : i - 1]
        key, typ = m.group(2), m.group(1).lower()
        if key in seen:
            raise CvError(
                f"{path}: duplicate citation key {key!r}. BibTeX silently keeps "
                f"one entry and drops the other, so one of your papers would "
                f"vanish. Rename one of them."
            )
        seen[key] = True
        entries.append({"key": key, "type": typ, "fields": _split_fields(body)})
    if not entries:
        raise CvError(f"{path}: no BibTeX entries found")
    return entries


def classify(entry, overrides):
    """journal | conference | preprint | thesis."""
    key, typ, f = entry["key"], entry["type"], entry["fields"]
    forced = overrides.get(key, {}).get("class")
    if forced:
        if forced not in ("journal", "conference", "preprint", "thesis"):
            raise CvError(f"publications.overrides.{key}.class: unknown value {forced!r}")
        return forced
    journal = f.get("journal", "")
    if re.search(r"arxiv|preprint|biorxiv", journal, re.I):
        return "preprint"
    if re.search(r"universit", f.get("publisher", ""), re.I) and not journal \
            and not f.get("booktitle"):
        return "thesis"
    if typ in ("inproceedings", "conference", "incollection"):
        return "conference"
    return "journal"


def split_authors(raw):
    return [a.strip() for a in re.split(r"\s+and\s+", raw) if a.strip()]


def _is_me(author, me_keys):
    norm = re.sub(r"\.", "", to_unicode(author)).strip().lower()
    return any(re.sub(r"\.", "", k).strip().lower() == norm for k in me_keys)


def author_initials(author):
    """`Zancanaro, Alberto` -> `A.~Zancanaro`; `Alberto Zancanaro` likewise."""
    a = to_unicode(author)
    if a in ("others", "and others"):
        return "et al."
    if "," in a:
        last, _, first = a.partition(",")
    else:
        bits = a.split()
        last, first = (bits[-1], " ".join(bits[:-1])) if len(bits) > 1 else (a, "")
    inits = " ".join(f"{p[0]}." for p in first.split() if p)
    last = last.strip()
    return f"{inits}~{last}" if inits else last


def author_full(author):
    """`Zancanaro, Alberto` -> `Alberto Zancanaro`, for the web outputs."""
    a = to_unicode(author)
    if a in ("others", "and others"):
        return "et al."
    if "," in a:
        last, _, first = a.partition(",")
        return f"{first.strip()} {last.strip()}".strip()
    return a


def authors_tex(raw, me_keys):
    out = []
    for a in split_authors(raw):
        if a == "others":
            out.append("et al.")
        elif _is_me(a, me_keys):
            out.append(r"\me")
        else:
            out.append(author_initials(a))
    return ", ".join(out)


def authors_web(raw):
    return [author_full(a) for a in split_authors(raw)]


def venue(entry):
    """The `Journal, vol(no), pages, year` half of a reference."""
    f = entry["fields"]
    bits = []
    place = f.get("journal") or f.get("booktitle") or f.get("publisher") or ""
    if place:
        bits.append(place)
    if f.get("volume"):
        v = f["volume"]
        if f.get("number"):
            v += f"({f['number']})"
        bits.append(v)
    if f.get("pages"):
        bits.append("pp. " + f["pages"].replace("--", "-"))
    if f.get("year"):
        bits.append(f["year"])
    return ", ".join(bits)


def link(entry, overrides):
    o = overrides.get(entry["key"], {})
    if o.get("url"):
        return o["url"]
    f = entry["fields"]
    if f.get("doi"):
        doi = f["doi"]
        return doi if doi.startswith("http") else f"https://doi.org/{doi}"
    return f.get("url", "")
