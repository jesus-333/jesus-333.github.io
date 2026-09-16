#!/usr/bin/env python3
"""common_material/cv.toml -> assets/json/resume.json (JSON Resume format).

The site loads this into site.data.resume via jekyll-get-json. It is only
rendered when _pages/cv.md sets `cv_format: jsonresume`; it is generated
regardless so the two never disagree if you switch.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cvlib import bib as bibmod
from cvlib import cli, emit, web
from cvlib.latex import strip_todo as _s
from cvlib.load import load


def build(data, entries):
    b = data["basics"]
    loc = b.get("location", {})
    basics = {
        "name": _s(b["name"]),
        "label": _s(b.get("label", "")),
        "image": b.get("image", ""),
        "email": b.get("email", ""),
    }
    # The phone number is only published when explicitly opted in --
    # assets/json/resume.json is served publicly whether or not the page
    # renders from it.
    if b.get("phone_public"):
        basics["phone"] = b.get("phone", "")
    basics["summary"] = _s(b.get("summary", "")).strip()
    basics["location"] = {
        "address": loc.get("street", ""),
        "postalCode": loc.get("postal_code", ""),
        "city": loc.get("city", ""),
        "countryCode": loc.get("country_code", ""),
        "region": loc.get("region", ""),
    }
    basics["profiles"] = [
        {"network": l["network"], "username": _s(l["username"]), "url": l.get("url", "")}
        for l in data.get("links", []) if l.get("site")
    ]
    return {
        "basics": basics,
        "work": web.experience(data, json_shape=True),
        "volunteer": web.experience(data, json_shape=True, volunteer=True),
        "education": web.education(data, json_shape=True),
        "publications": web.publications(data, entries, json_shape=True),
        "skills": web.skills(data, json_shape=True),
        "languages": web.languages(data, json_shape=True),
        "projects": web.projects(data, json_shape=True),
    }


def main():
    args = cli.parser(__doc__, default_out="assets/json/resume.json",
                      todo_gate=True).parse_args()
    data = load(args.toml)
    cli.gate_todo(data, args, "assets/json/resume.json")
    entries = bibmod.parse(cli.rel(data["publications"]["bib"]))
    web.check_keys(data, entries)

    payload = build(data, entries)
    # JSON has no comment syntax, so the banner lives in a leading key
    # rather than above the document.
    payload = {"_generated": "by bin/cv/build_resume_json.py from "
                             "common_material/cv.toml -- do not edit", **payload}
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if emit.write(cli.rel(args.out), content, check=args.check):
        if args.check:
            print(f"ok: {args.out} is up to date")
    else:
        print(f"wrote {args.out}")


cli.run(main)
