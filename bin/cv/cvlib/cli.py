"""Argument parsing and the top-level error handler shared by every script."""

import argparse
import os
import sys

from .errors import CvError
from .load import REPO


def parser(description, *, default_out, todo_gate=False):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--toml", default=None, help="path to cv.toml")
    p.add_argument("-o", "--out", default=default_out, help="output path")
    p.add_argument("--check", action="store_true",
                   help="do not write; fail if the file on disk is out of date")
    if todo_gate:
        p.add_argument("--allow-todo", action="store_true",
                       help="permit unresolved @TODO placeholders in a public output")
    return p


def run(main):
    try:
        sys.exit(main() or 0)
    except CvError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)


def rel(path):
    return os.path.join(REPO, path) if not os.path.isabs(path) else path


def gate_todo(data, args, target):
    from .load import has_todo

    found = has_todo(data)
    if found and not getattr(args, "allow_todo", False):
        raise CvError(
            f"{target} would publish {len(found)} unresolved placeholder(s):\n"
            + "\n".join(f"    {f}" for f in found)
            + "\n  Fill them in in common_material/cv.toml, or pass --allow-todo if "
              "you really mean to publish them.\n"
              "  (Entries marked `todo = true` are dropped from the website "
              "either way; this gate is about the rest.)"
        )
