"""Read and validate common_material/cv.toml."""

import os
import tomllib

from .errors import CvError
from . import latex

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_TOML = os.path.join(REPO, "common_material", "cv.toml")

# Every key the generators understand. An unknown key is an error, not a
# silent drop: a typo'd field would otherwise disappear without a word.
_KNOWN = {
    "root": {"schema_version", "basics", "links", "tex", "site", "sections",
             "education", "experience", "skills", "languages", "projects",
             "projects_note", "publications", "profiles"},
    "basics": {"name", "label", "email", "email_alt", "phone", "phone_uri",
               "phone_public", "image", "citizenship", "summary", "location"},
    "location": {"display", "city", "region", "postal_code", "street", "country_code"},
    "links": {"id", "network", "username", "url", "tex_label", "tex_icon", "site", "todo"},
    "education": {"id", "institution", "unit", "url", "location", "study_type",
                  "area", "start", "end", "score", "courses", "thesis",
                  "highlights", "todo"},
    "experience": {"id", "position", "company", "unit", "location", "url",
                   "start", "end", "kind", "summary", "highlights", "todo"},
    "skills": {"name", "icon", "level", "keywords"},
    "languages": {"name", "fluency", "inline", "note", "todo"},
    "projects": {"id", "name", "url", "stack", "summary", "highlights",
                 "start", "end", "featured", "todo"},
    "publications": {"bib", "me_author_keys", "exclude", "featured", "overrides"},
    "profile": {"tagline", "experience", "projects", "publications_short", "skill_order"},
}

_KINDS = {"research", "teaching", "industry", "volunteer"}


def _check_keys(obj, allowed, where):
    for k in obj:
        base = k[:-4] if k.endswith("_tex") else k
        if base not in allowed:
            raise CvError(
                f"{where}: unknown key {k!r}. Known keys: "
                f"{', '.join(sorted(allowed))}."
            )


def field(obj, name, where):
    """Resolve a `<name>` / `<name>_tex` pair.

    Returns (web_value, tex_value). The _tex sibling wins for LaTeX and is
    emitted verbatim; the plain value always feeds the website.
    """
    plain = obj.get(name, "")
    raw = obj.get(name + "_tex")
    if raw is not None:
        if not plain:
            raise CvError(
                f"{where}.{name}_tex is set but {name} is not. The plain field "
                f"feeds the website and cannot be omitted."
            )
        return latex.strip_todo(plain), latex.verbatim_check(raw, f"{where}.{name}_tex")
    return latex.strip_todo(plain), latex.tex_todo(plain)


def load(path=None):
    path = path or DEFAULT_TOML
    if not os.path.exists(path):
        raise CvError(f"{path}: not found")
    with open(path, "rb") as fh:
        data = tomllib.load(fh)

    _check_keys(data, _KNOWN["root"], "cv.toml")
    if data.get("schema_version") != 1:
        raise CvError(f"cv.toml: unsupported schema_version {data.get('schema_version')!r}")

    _check_keys(data["basics"], _KNOWN["basics"], "[basics]")
    _check_keys(data["basics"].get("location", {}), _KNOWN["location"], "[basics.location]")
    for i, e in enumerate(data.get("links", [])):
        _check_keys(e, _KNOWN["links"], f"[[links]] #{i + 1}")
    for sec in ("education", "experience", "skills", "languages", "projects"):
        for i, e in enumerate(data.get(sec, [])):
            _check_keys(e, _KNOWN[sec], f"[[{sec}]] #{i + 1}")
    _check_keys(data.get("publications", {}), _KNOWN["publications"], "[publications]")
    for name, prof in data.get("profiles", {}).items():
        _check_keys(prof, _KNOWN["profile"], f"[profiles.{name}]")

    for e in data.get("experience", []):
        if e.get("kind", "research") not in _KINDS:
            raise CvError(
                f"[[experience]] {e.get('id')}: kind={e.get('kind')!r} is not one of "
                f"{', '.join(sorted(_KINDS))}"
            )
    _unique_ids(data)
    return data


def _unique_ids(data):
    for sec in ("education", "experience", "projects", "links"):
        seen = set()
        for e in data.get(sec, []):
            i = e.get("id")
            if not i:
                raise CvError(f"[[{sec}]]: every entry needs an id (profiles reference them)")
            if i in seen:
                raise CvError(f"[[{sec}]]: duplicate id {i!r}")
            seen.add(i)


def profile(data, name):
    profs = data.get("profiles", {})
    if name not in profs:
        raise CvError(
            f"unknown profile {name!r}. Defined profiles: "
            f"{', '.join(sorted(profs)) or '(none)'}"
        )
    return profs[name]


def select(entries, ids, where):
    """Order `entries` by an explicit id list, erroring on an unknown id.

    This check is load-bearing, not cosmetic: a renamed id would otherwise
    silently drop a job from a tailored CV.
    """
    by_id = {e["id"]: e for e in entries}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise CvError(
            f"{where}: no entry with id {', '.join(repr(u) for u in unknown)}. "
            f"Available: {', '.join(sorted(by_id))}."
        )
    return [by_id[i] for i in ids]


def has_todo(data):
    """Every TODO marker still present anywhere in the tree."""
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            if node.get("todo") is True:
                found.append(f"{path} (todo = true)")
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and latex.has_todo(node):
            found.append(f"{path}: {node!r}")

    walk(data, "")
    return found
