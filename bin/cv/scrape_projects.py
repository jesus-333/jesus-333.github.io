#!/usr/bin/env python3
"""_projects/*.md -> cv_tex/generated/projects_site.tex

A convenience feed, NOT a source of truth: no driver \\input()s it. The
curated project list lives in common_material/cv.toml, because the CV
wants four sharp entries and the website wants all of them.

Use it when you have added real project pages: run it, read the output,
and move the entries you want into cv.toml.
"""

import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml

from cvlib import cli, emit, latex
from cvlib.errors import CvError

GEN = "bin/cv/scrape_projects.py"

# Lines that are markup rather than prose. A project body that opens with
# a figure include or a raw <div> has no usable first paragraph, and
# guessing produces garbage in the PDF.
_MARKUP = re.compile(r"^\s*(?:\{%|\{\{|<|#{1,6}\s|```|~~~|\||\s{4,}\S)")


def front_matter(text, path):
    if not text.startswith("---"):
        raise CvError(f"{path}: no YAML front matter")
    _, fm, body = text.split("---", 2)
    try:
        meta = yaml.safe_load(fm) or {}
    except yaml.YAMLError as exc:
        raise CvError(f"{path}: malformed front matter: {exc}")
    return meta, body.lstrip("\n")


def first_paragraph(body):
    """The first run of prose lines, soft-wraps joined. None if there is none."""
    for block in re.split(r"\n\s*\n", body):
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines or any(_MARKUP.match(l) for l in lines):
            continue
        para = " ".join(l.strip() for l in lines)
        # Strip inline Liquid and HTML that survived inside a prose line.
        para = re.sub(r"\{%.*?%\}|\{\{.*?\}\}|<[^>]+>", "", para).strip()
        if para:
            return re.sub(r"\s+", " ", para)
    return None


def collect(srcdir):
    rows = []
    for path in sorted(glob.glob(os.path.join(srcdir, "*.md"))):
        meta, body = front_matter(open(path, encoding="utf-8").read(), path)
        if meta.get("redirect"):
            continue  # an external link, not a project page
        title = meta.get("title")
        if not title:
            raise CvError(f"{path}: front matter has no `title`")
        summary = meta.get("description") or first_paragraph(body)
        if not summary:
            sys.stderr.write(
                f"warning: {os.path.basename(path)} has no `description` and no "
                f"usable first paragraph; skipped\n")
            continue
        rows.append({
            "title": str(title),
            "summary": str(summary),
            "importance": meta.get("importance", 999),
            "category": meta.get("category", ""),
            "path": os.path.basename(path),
        })
    return sorted(rows, key=lambda r: (str(r["category"]), r["importance"], r["path"]))


def render(rows, srcdir):
    out = [emit.banner("%", GEN).replace(
        "Source:    common_material/cv.toml", f"Source:    {srcdir}/*.md")]
    out.append("")
    out.append("% Not \\input by any driver. Scraped from the website's project")
    out.append("% pages so you can lift entries into common_material/cv.toml.")
    out.append("")
    for r in rows:
        out.append("%% %s (%s, importance %s)" % (r["path"], r["category"] or "-", r["importance"]))
        out.append(r"\cvproject{%s}{}" % latex.escape(r["title"]))
        out.append(r"  {%s}" % latex.escape(r["summary"]))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _warn_unprintable(rows):
    """pdflatex cannot typeset emoji and similar; say so rather than emit a
    file that dies at compile time if it is ever \\input."""
    for r in rows:
        bad = {c for c in r["title"] + r["summary"] if ord(c) > 0x2100}
        if bad:
            sys.stderr.write(
                f"warning: {r['path']} contains characters pdfLaTeX cannot "
                f"typeset ({''.join(sorted(bad))}); remove them before using "
                f"this entry\n")


def main():
    p = cli.parser(__doc__, default_out="cv_tex/generated/projects_site.tex")
    p.add_argument("--src", default="_projects", help="directory of project pages")
    args = p.parse_args()

    rows = collect(cli.rel(args.src))
    _warn_unprintable(rows)
    if not rows:
        raise CvError(f"{args.src}: no usable project pages found")
    content = render(rows, args.src)
    if emit.write(cli.rel(args.out), content, check=args.check):
        if args.check:
            print(f"ok: {args.out} is up to date")
    else:
        print(f"wrote {args.out} ({len(rows)} projects)")


cli.run(main)
