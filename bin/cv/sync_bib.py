#!/usr/bin/env python3
"""common_material/papers.bib -> the two places that need a copy.

  _bibliography/papers.bib    jekyll-scholar renders /publications/ from it,
                              and requires an empty YAML front-matter fence.
  cv_tex/generated/papers.bib plain copy, so cv_tex/ stays a self-contained
                              Overleaf project.

Also refuses to run on a duplicate citation key: BibTeX silently keeps one
entry and discards the other, so a duplicate makes a paper disappear.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cvlib import bib as bibmod
from cvlib import cli, emit
from cvlib.load import REPO

GEN = "bin/cv/sync_bib.py"
TARGETS = ["_bibliography/papers.bib", "cv_tex/generated/papers.bib"]


def main():
    p = cli.parser(__doc__, default_out="")
    p.add_argument("--src", default="common_material/papers.bib")
    args = p.parse_args()

    src = cli.rel(args.src)
    entries = bibmod.parse(src)          # raises on a duplicate key
    body = open(src, encoding="utf-8").read().lstrip()

    banner = emit.banner("%", GEN).replace(
        "Source:    common_material/cv.toml", f"Source:    {args.src}")
    unchanged = 0
    for target in TARGETS:
        # jekyll-scholar needs the bare `---` fence as the first thing in
        # the file, so the banner goes after it, not before.
        head = "---\n---\n\n" if target.startswith("_bibliography/") else ""
        content = head + banner + "\n" + body
        if emit.write(cli.rel(target), content, check=args.check):
            unchanged += 1

    _warn_scholar_name()
    if args.check:
        print(f"ok: {unchanged}/{len(TARGETS)} bib copies up to date "
              f"({len(entries)} entries)")
    else:
        print(f"synced {len(entries)} entries to {', '.join(TARGETS)}")


def _warn_scholar_name():
    """jekyll-scholar bolds an author by name; a stale one bolds nobody."""
    cfg = os.path.join(REPO, "_config.yml")
    if not os.path.exists(cfg):
        return
    text = open(cfg, encoding="utf-8").read()
    if "Zancanaro" not in text:
        sys.stderr.write(
            "warning: _config.yml scholar.last_name does not mention Zancanaro, "
            "so no author will be bolded on /publications/\n")


cli.run(main)
