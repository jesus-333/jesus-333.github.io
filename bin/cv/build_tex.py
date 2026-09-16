#!/usr/bin/env python3
"""common_material/cv.toml -> cv_tex/generated/*.tex

Emits the structured half of the LaTeX CV. The prose half --
cv_tex/sections/summary.tex and legal_it.tex -- is hand-written and is
never touched by this script.

A profile (--profile) selects and orders existing entries by id. It
never introduces new text: that is what keeps the source of truth
single while still allowing a CV tailored per application.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cvlib import bib as bibmod
from cvlib import cli, dates, emit, latex
from cvlib.errors import CvError
from cvlib.load import field, load, profile, select

GEN = "bin/cv/build_tex.py"
RESERVED = {"phone", "email", "email_alt", "location", "citizenship"}


def _banner(prof):
    return emit.banner("%", GEN, profile=prof)


def _tex(obj, name, where):
    return field(obj, name, where)[1]


# --------------------------------------------------------------------- header
def personal_data(data, prof_name, prof):
    b = data["basics"]
    links = {l["id"]: l for l in data.get("links", [])}
    out = [_banner(prof_name), ""]

    tagline = prof.get("tagline") or ""
    if tagline:
        tagline_tex = latex.tex_todo(tagline)
    else:
        tagline_tex = _tex(b, "label", "[basics]")

    out.append(r"\newcommand{\cvName}{%s}" % _tex(b, "name", "[basics]"))
    out.append(r"\newcommand{\cvTagline}{%s}" % tagline_tex)
    out.append("")
    out.append(r"\newcommand{\cvPhone}{%s}" % latex.escape(b.get("phone", "")))
    out.append(r"\newcommand{\cvPhoneURI}{%s}" % latex.url(b.get("phone_uri", ""), "[basics].phone_uri"))
    out.append(r"\newcommand{\cvEmail}{%s}" % latex.escape(b.get("email", "")))
    out.append(r"\newcommand{\cvEmailAlt}{%s}" % latex.escape(b.get("email_alt", "")))
    for lid, l in links.items():
        out.append(r"\newcommand{\cvLink%s}{%s}" % (_camel(lid), latex.tex_todo(l.get("username", ""))))
    out.append("")
    out.append(r"\newcommand{\cvLocation}{%s}" %
               _tex(b.get("location", {}), "display", "[basics.location]"))
    out.append(r"\newcommand{\cvCitizenship}{%s}" % _tex(b, "citizenship", "[basics]"))
    out.append("")

    hdr = data.get("tex", {}).get("header", {})
    for name, key in (("One", "line_one"), ("Two", "line_two"), ("Three", "line_three")):
        items = [_header_item(tok, b, links, key) for tok in hdr.get(key, [])]
        if items:
            # Each item ends in a comment character so the source newline does
            # not become an inter-item space; \cvsep then sits on its own line,
            # exactly as the hand-written original did.
            body = "%\n  " + "%\n  \\cvsep\n  ".join(items) + "%\n"
        else:
            body = ""
        out.append(r"\newcommand{\cvContactLine%s}{%s}" % (name, body))
        out.append("")

    inline = ", ".join(
        "%s (%s)" % (latex.escape(l["name"]), latex.tex_todo(l.get("inline") or l.get("fluency", "")))
        for l in data.get("languages", []))
    out.append(r"\newcommand{\cvLanguagesInline}{%s}" % inline)
    rows = "\n  ".join(
        r"\cvrow{%s}{%s}" % (latex.escape(l["name"]), _fluency(l))
        for l in data.get("languages", []))
    out.append(r"\newcommand{\cvLanguagesRows}{%%%s%s}" % ("\n  " + rows if rows else "", "\n"))
    return "\n".join(out) + "\n"


def _camel(s):
    return "".join(p.capitalize() for p in s.replace("_", "-").split("-"))


def _fluency(l):
    f = latex.tex_todo(l.get("fluency", ""))
    if l.get("note"):
        return f + " -- " + latex.tex_todo(l["note"])
    return f


def _header_item(token, b, links, where):
    if token == "phone":
        return r"\cvicon{\faIcon{phone-alt}}\href{tel:\cvPhoneURI}{\cvPhone}"
    if token == "email":
        return r"\cvicon{\faIcon{envelope}}\href{mailto:\cvEmail}{\cvEmail}"
    if token == "email_alt":
        return r"\cvicon{\faIcon{envelope-open}}\href{mailto:\cvEmailAlt}{\cvEmailAlt}"
    if token == "location":
        return r"\cvicon{\faIcon{map-marker-alt}}\cvLocation"
    if token == "citizenship":
        return r"\cvCitizenship"
    if token in links:
        l = links[token]
        return r"\cvicon{\faIcon{%s}}\href{%s}{%s}" % (
            l.get("tex_icon", "link"),
            latex.url(l.get("url", ""), f"[[links]] {token}.url"),
            latex.tex_todo(l.get("tex_label") or l.get("username", "")),
        )
    raise CvError(
        f"[tex.header].{where}: unknown token {token!r}. Use a [[links]].id or "
        f"one of {', '.join(sorted(RESERVED))}."
    )


# ------------------------------------------------------------------ education
def education(data, prof_name):
    title = latex.escape(data["sections"]["education"]["tex_title"])
    out = [_banner(prof_name), "", r"\section{%s}" % title, ""]
    rows = sorted(data.get("education", []),
                  key=lambda x: dates.sort_key(x.get("end"), "education.end", end=True),
                  reverse=True)
    for e in rows:
        w = f"[[education]] {e['id']}"
        left = ", ".join(x for x in [
            "%s in %s" % (_tex(e, "study_type", w), _tex(e, "area", w)),
            _tex(e, "institution", w), latex.escape(e.get("unit", "")),
        ] if x.strip())
        out.append(r"\cvcompactentry{%s}{%s}" % (left, dates.tex_range(e.get("start"), e.get("end"), w)))
        detail = []
        if e.get("courses"):
            detail.append("Curriculum: " + ", ".join(latex.escape(c) for c in e["courses"]) + ".")
        if e.get("thesis"):
            detail.append(r"Thesis: \emph{%s}." % _tex(e, "thesis", w))
        for h in e.get("highlights", []):
            detail.append(latex.tex_todo(h))
        if detail:
            out.append(r"\cvdetail{%s}" % " ".join(detail))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ----------------------------------------------------------------- experience
def experience(data, prof_name, prof):
    title = latex.escape(data["sections"]["experience"]["tex_title"])
    out = [_banner(prof_name), "", r"\section{%s}" % title, ""]
    ids = prof.get("experience")
    rows = select(data["experience"], ids, f"[profiles.{prof_name}].experience") if ids else \
        sorted(data["experience"],
               key=lambda x: dates.sort_key(x.get("end"), "experience.end", end=True),
               reverse=True)
    for e in rows:
        w = f"[[experience]] {e['id']}"
        todo = e.get("todo", False)
        wrap = (lambda s: r"\cvTODO{%s}" % s) if todo else (lambda s: s)
        org = ", ".join(x for x in [_tex(e, "company", w), latex.escape(e.get("unit", ""))] if x.strip())
        out.append(r"\cventry{%s}{%s}{%s}{%s}" % (
            wrap(_tex(e, "position", w)), wrap(org),
            wrap(_tex(e, "location", w)),
            wrap(dates.tex_range(e.get("start"), e.get("end"), w)),
        ))
        if e.get("summary"):
            out.append(r"\cvdetail{%s}" % wrap(_tex(e, "summary", w)))
        if e.get("highlights"):
            out.append(r"\begin{cvbullets}")
            for h in e["highlights"]:
                out.append(r"  \item %s" % wrap(latex.tex_todo(h)))
            out.append(r"\end{cvbullets}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------------- skills
def skills(data, prof_name, prof):
    title = latex.escape(data["sections"]["skills"]["tex_title"])
    rows = data.get("skills", [])
    order = prof.get("skill_order")
    if order:
        by_name = {s["name"]: s for s in rows}
        missing = [n for n in order if n not in by_name]
        if missing:
            raise CvError(
                f"[profiles.{prof_name}].skill_order: no [[skills]] named "
                f"{', '.join(repr(m) for m in missing)}. Available: "
                f"{', '.join(sorted(by_name))}."
            )
        rows = [by_name[n] for n in order] + [s for s in rows if s["name"] not in order]
    out = [_banner(prof_name), "", r"\section{%s}" % title, "",
           r"\begin{cvtable}[0.23\linewidth]"]
    for s in rows:
        out.append(r"  \cvrow{%s}{%s}" % (
            latex.escape(s["name"]),
            ", ".join(latex.escape(k) for k in s.get("keywords", []))))
    out.append(r"  % The long CV gives spoken languages their own section instead.")
    out.append(r"  \ifcvlongform\else\cvrow{Spoken languages}{\cvLanguagesInline}\fi")
    out.append(r"\end{cvtable}")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ languages
def languages(data, prof_name):
    title = latex.escape(data["sections"]["languages"]["tex_title"])
    return "\n".join([
        _banner(prof_name), "",
        "% Long-form variant only; the one-page CV folds these into the skills table.",
        r"\section{%s}" % title, "",
        r"\begin{cvtable}[0.23\linewidth]",
        r"  \cvLanguagesRows",
        r"\end{cvtable}",
    ]) + "\n"


# ------------------------------------------------------------------- projects
def projects(data, prof_name, prof):
    title = latex.escape(data["sections"]["projects"]["tex_title"])
    out = [_banner(prof_name), "", r"\section{%s}" % title, ""]

    note = data.get("projects_note")
    if note:
        links = {l["id"]: l for l in data.get("links", [])}
        target = links.get(note.get("link", ""), {})
        tail = latex.href(target.get("url", ""), latex.escape(target.get("tex_label", "")),
                          "[projects_note].link") if target else ""
        out.append(r"\cvdetail{%s%s}" % (latex.escape(note.get("text", "")),
                                         (" " + tail + ".") if tail else ""))
        out.append("")

    ids = prof.get("projects")
    rows = select(data["projects"], ids, f"[profiles.{prof_name}].projects") if ids else \
        [p for p in data["projects"] if p.get("featured", True)]
    for p in rows:
        w = f"[[projects]] {p['id']}"
        name = latex.href(p.get("url", ""), _tex(p, "name", w), w + ".url")
        out.append(r"\cvproject{%s}{%s}" % (name, ", ".join(latex.escape(s) for s in p.get("stack", []))))
        out.append(r"  {%s}" % _tex(p, "summary", w))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------- publications
_CLASS_TITLE = [("journal", "Journal articles"), ("conference", "Conference papers"),
                ("preprint", "Preprints"), ("thesis", "Theses")]


def _entry_tex(e, cfg, overrides):
    f = e["fields"]
    return r"  \cvpublication{%s}" % bibmod.authors_tex(f.get("author", ""),
                                                        cfg.get("me_author_keys", [])) + \
        "\n                {%s}{%s}{%s}" % (
            f.get("title", ""), bibmod.venue(e),
            latex.url(bibmod.link(e, overrides), f"bib[{e['key']}].url"))


def publications(data, prof_name, prof, entries, *, full):
    cfg = data.get("publications", {})
    overrides = cfg.get("overrides", {})
    exclude = set(cfg.get("exclude", []))
    title = latex.escape(data["sections"]["publications"]["tex_title"])
    links = {l["id"]: l for l in data.get("links", [])}
    out = [_banner(prof_name), "", r"\section{%s}" % title, ""]

    keep = [e for e in entries if e["key"] not in exclude]
    if full:
        by_class = {}
        for e in keep:
            by_class.setdefault(bibmod.classify(e, overrides), []).append(e)
        for cls, heading in _CLASS_TITLE:
            group = sorted(by_class.get(cls, []),
                           key=lambda x: x["fields"].get("year", "0"), reverse=True)
            if not group:
                continue
            out.append(r"\subsection*{%s}" % heading)
            out.append(r"\begin{cvpublications}")
            out += [_entry_tex(e, cfg, overrides) for e in group]
            out.append(r"\end{cvpublications}")
            out.append("")
    else:
        wanted = prof.get("publications_short") or cfg.get("featured", [])
        known = {e["key"]: e for e in keep}
        missing = [k for k in wanted if k not in known]
        if missing:
            raise CvError(
                f"[profiles.{prof_name}].publications_short: {', '.join(missing)} "
                f"is not a selectable citation key (excluded, or absent from the bib)."
            )
        out.append(r"\begin{cvpublications}")
        out += [_entry_tex(known[k], cfg, overrides) for k in wanted]
        out.append(r"\end{cvpublications}")
        out.append("")

    orcid, scholar = links.get("orcid"), links.get("scholar")
    if orcid and scholar:
        out.append(r"\vspace{2pt}")
        out.append(r"{\small Complete list:")
        out.append(r"\href{%s}{ORCID %s} \textbullet{}" % (
            latex.url(orcid["url"], "orcid.url"), latex.escape(orcid["username"])))
        out.append(r"\href{%s}{Google Scholar}.}" % latex.url(scholar["url"], "scholar.url"))
    return "\n".join(out).rstrip() + "\n"


def main():
    p = cli.parser(__doc__, default_out="cv_tex/generated")
    p.add_argument("--profile", default="default", help="tailoring profile from cv.toml")
    args = p.parse_args()

    data = load(args.toml)
    prof = profile(data, args.profile)
    entries = bibmod.parse(cli.rel(data["publications"]["bib"]))
    from cvlib import web
    web.check_keys(data, entries)

    files = {
        "personal_data.tex": personal_data(data, args.profile, prof),
        "education.tex": education(data, args.profile),
        "experience.tex": experience(data, args.profile, prof),
        "skills.tex": skills(data, args.profile, prof),
        "languages.tex": languages(data, args.profile),
        "projects.tex": projects(data, args.profile, prof),
        "publications_short.tex": publications(data, args.profile, prof, entries, full=False),
        "publications_full.tex": publications(data, args.profile, prof, entries, full=True),
    }
    outdir = cli.rel(args.out)
    unchanged = 0
    for name, content in files.items():
        if emit.write(os.path.join(outdir, name), content, check=args.check):
            unchanged += 1
    if args.check:
        print(f"ok: {unchanged}/{len(files)} generated .tex files up to date")
    else:
        print(f"wrote {len(files)} files to {args.out} (profile: {args.profile})")


cli.run(main)
