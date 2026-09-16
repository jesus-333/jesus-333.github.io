#!/usr/bin/env python3
"""common_material/cv.toml -> _data/cv.yml (rendercv format).

This is the file the website's /cv/ page actually renders, via the
al_folio_cv gem and `cv_format: rendercv` in _pages/cv.md.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml

from cvlib import bib as bibmod
from cvlib import cli, emit, web
from cvlib.errors import CvError
from cvlib.latex import strip_todo as _s
from cvlib.load import load

BUILDERS = {
    "Education": lambda d, e: web.education(d, json_shape=False),
    "Experience": lambda d, e: web.experience(d, json_shape=False),
    "Volunteer": lambda d, e: web.experience(d, json_shape=False, volunteer=True),
    "Projects": lambda d, e: web.projects(d, json_shape=False),
    "Publications": lambda d, e: web.publications(d, e, json_shape=False),
    "Skills": lambda d, e: web.skills(d, json_shape=False),
    "Languages": lambda d, e: web.languages(d, json_shape=False),
}


def build(data, entries):
    b = data["basics"]
    loc = b.get("location", {})
    cv = {
        "name": _s(b["name"]),
        "label": _s(b.get("label", "")),
        "email": b.get("email", ""),
        "location": _s(loc.get("display", "")),
        "image": b.get("image", ""),
        "summary": _s(b.get("summary", "")).strip(),
    }
    socials = [{"network": l["network"], "username": _s(l["username"])}
               for l in data.get("links", []) if l.get("site")]
    if socials:
        cv["social_networks"] = socials
    if any(loc.get(k) for k in ("street", "city", "region", "postal_code", "country_code")):
        cv["address"] = {
            "street": loc.get("street", ""),
            "city": loc.get("city", ""),
            "region": loc.get("region", ""),
            # camelCase here and snake_case elsewhere is the shipped
            # template's own inconsistency, not a typo.
            "postalCode": loc.get("postal_code", ""),
            "countryCode": loc.get("country_code", ""),
        }

    sections = {}
    for name in data["site"]["section_order"]:
        if name not in BUILDERS:
            raise CvError(
                f"[site].section_order: {name!r} has no builder. Known sections: "
                f"{', '.join(BUILDERS)}."
            )
        rows = BUILDERS[name](data, entries)
        if rows:
            sections[name] = rows
    cv["sections"] = sections
    return {"cv": cv}


def main():
    args = cli.parser(__doc__, default_out="_data/cv.yml", todo_gate=True).parse_args()
    data = load(args.toml)
    cli.gate_todo(data, args, "_data/cv.yml")
    entries = bibmod.parse(cli.rel(data["publications"]["bib"]))
    web.check_keys(data, entries)

    body = yaml.safe_dump(build(data, entries), sort_keys=False, allow_unicode=True,
                          width=4096, default_flow_style=False, indent=2)
    content = emit.banner("#", "bin/cv/build_cv_yml.py") + "\n" + body
    if emit.write(cli.rel(args.out), content, check=args.check):
        if args.check:
            print(f"ok: {args.out} is up to date")
    else:
        print(f"wrote {args.out}")


cli.run(main)
