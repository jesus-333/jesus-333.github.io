"""Shared shaping for the two website outputs.

_data/cv.yml (rendercv) and assets/json/resume.json (JSON Resume) carry
the same facts under different key names. The differences are hard-coded
here rather than derived, because they are arbitrary: `company` vs
`name`, `title` vs `name`, string vs array for keywords.
"""

from . import bib as bibmod
from . import dates
from .errors import CvError
from .latex import strip_todo as _s


def visible(entries):
    """Entries not marked `todo = true` never reach a public page."""
    return [e for e in entries if not e.get("todo")]


def csv(values):
    return ", ".join(values or [])


def _thesis_highlights(e):
    out = []
    if e.get("courses"):
        out.append("Curriculum: " + csv(e["courses"]) + ".")
    if e.get("thesis"):
        out.append("Thesis: " + _s(e["thesis"]) + ".")
    out += [_s(h) for h in e.get("highlights", [])]
    return out


def education(data, *, json_shape):
    rows = []
    for e in sorted(visible(data.get("education", [])),
                    key=lambda x: dates.sort_key(x.get("end"), "education.end", end=True),
                    reverse=True):
        w = f"education[{e['id']}]"
        row = {
            "institution": _s(e.get("institution", "")),
            "location": _s(e.get("location", "")),
        }
        if e.get("url"):
            row["url"] = e["url"]
        row["area"] = _s(e.get("area", ""))
        row["studyType"] = _s(e.get("study_type", ""))
        _dates(row, e, w, json_shape)
        if e.get("score"):
            row["score"] = e["score"]
        courses = e.get("courses", [])
        if courses:
            row["courses"] = courses if json_shape else csv(courses)
        hl = _thesis_highlights(e)
        if hl:
            row["highlights"] = hl
        rows.append(row)
    return rows


def _dates(row, e, where, json_shape):
    if json_shape:
        s = dates.to_jsonresume(e.get("start"), where + ".start")
        t = dates.to_jsonresume(e.get("end"), where + ".end", end=True)
        if s:
            row["startDate"] = s
        if t:
            row["endDate"] = t
    else:
        s = dates.to_rendercv(e.get("start"), where + ".start")
        t = dates.to_rendercv(e.get("end"), where + ".end")
        if s is not None:
            row["start_date"] = s
        if t is not None:
            row["end_date"] = t


def experience(data, *, json_shape, volunteer=False):
    rows = []
    wanted = (lambda k: k == "volunteer") if volunteer else (lambda k: k != "volunteer")
    picked = [e for e in visible(data.get("experience", []))
              if wanted(e.get("kind", "research"))]
    for e in sorted(picked,
                    key=lambda x: dates.sort_key(x.get("end"), "experience.end", end=True),
                    reverse=True):
        w = f"experience[{e['id']}]"
        org = _s(e.get("company", ""))
        row = {}
        if json_shape:
            row["organization" if volunteer else "name"] = org
        else:
            row["company"] = org
        row["position"] = _s(e.get("position", ""))
        row["location"] = _s(e.get("location", ""))
        if json_shape and e.get("url"):
            row["url"] = e["url"]
        _dates(row, e, w, json_shape)
        row["summary"] = _s(e.get("summary", ""))
        row["highlights"] = [_s(h) for h in e.get("highlights", [])]
        rows.append(row)
    return rows


def skills(data, *, json_shape):
    rows = []
    for s in data.get("skills", []):
        row = {"name": _s(s["name"]), "level": s.get("level", "")}
        if s.get("icon"):
            row["icon"] = s["icon"]
        kw = [_s(k) for k in s.get("keywords", [])]
        row["keywords"] = kw if json_shape else csv(kw)
        rows.append(row)
    return rows


def languages(data, *, json_shape):
    rows = []
    for l in visible(data.get("languages", [])):
        fluency = _s(l.get("fluency", ""))
        if json_shape:
            rows.append({"language": _s(l["name"]), "fluency": fluency, "icon": ""})
        else:
            summary = fluency
            if l.get("note"):
                summary = f"{fluency} — {_s(l['note'])}"
            rows.append({"name": _s(l["name"]), "summary": summary})
    return rows


def projects(data, *, json_shape):
    rows = []
    for p in visible(data.get("projects", [])):
        if not p.get("featured", True):
            continue
        w = f"projects[{p['id']}]"
        row = {"name": _s(p["name"]), "summary": _s(p.get("summary", ""))}
        if p.get("highlights"):
            row["highlights"] = [_s(h) for h in p["highlights"]]
        if json_shape and p.get("url"):
            row["url"] = p["url"]
        if p.get("start") or p.get("end"):
            _dates(row, p, w, json_shape)
        rows.append(row)
    return rows


def publications(data, entries, *, json_shape):
    cfg = data.get("publications", {})
    overrides = cfg.get("overrides", {})
    exclude = set(cfg.get("exclude", []))
    rows = []
    keep = [e for e in entries if e["key"] not in exclude]
    for e in sorted(keep, key=lambda x: x["fields"].get("year", "0"), reverse=True):
        f = e["fields"]
        title = bibmod.to_unicode(f.get("title", ""))
        row = {}
        if json_shape:
            row["name"] = title
        else:
            row["title"] = title
            row["authors"] = bibmod.authors_web(f.get("author", ""))
        row["publisher"] = bibmod.to_unicode(
            f.get("journal") or f.get("booktitle") or f.get("publisher") or "")
        if f.get("year"):
            row["releaseDate"] = f"{f['year']}-01-01"
        url = bibmod.link(e, overrides)
        if url:
            row["url"] = url
        if f.get("abstract"):
            row["summary"] = bibmod.to_unicode(f["abstract"])
        rows.append(row)
    return rows


def check_keys(data, entries):
    """A selection key that names no bib entry is a silent dropped paper."""
    cfg = data.get("publications", {})
    known = {e["key"] for e in entries}
    for field_name in ("exclude", "featured"):
        for k in cfg.get(field_name, []):
            if k not in known:
                raise CvError(
                    f"[publications].{field_name}: {k!r} is not a citation key in "
                    f"{cfg.get('bib')}. Available keys start: "
                    f"{', '.join(sorted(known)[:5])}..."
                )
    for k in cfg.get("overrides", {}):
        if k not in known:
            raise CvError(f"[publications.overrides.{k}]: not a citation key in the bib")
