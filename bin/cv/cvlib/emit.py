"""Writing generated files, and the --check gate.

No timestamp and no version string in the banner: either would make
every regeneration a diff and would break the byte-for-byte idempotency
that --check relies on.
"""

import difflib
import os
import sys

from .errors import CvError

_LINES = [
    "GENERATED FILE -- DO NOT EDIT.",
    "Source:    common_material/cv.toml",
    "Generator: {gen}",
    "Edit the source and run `make cv`.",
]


def banner(comment, generator, *, profile=None, rule=None):
    rule = rule or ("=" * 69)
    lines = list(_LINES)
    if profile:
        lines.insert(2, f"Profile:   {profile}")
    body = [f"{comment} {rule}"]
    body += [f"{comment}  {ln.format(gen=generator)}" for ln in lines]
    body.append(f"{comment} {rule}")
    return "\n".join(body) + "\n"


def write(path, content, *, check=False):
    """Write, or in check mode diff against what is on disk.

    Returns True when the file on disk already matched.
    """
    existing = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            existing = fh.read()
    if existing == content:
        return True
    if check:
        diff = difflib.unified_diff(
            (existing or "").splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"{path} (on disk)",
            tofile=f"{path} (regenerated)",
        )
        sys.stderr.write("".join(diff))
        raise CvError(
            f"{path} is out of date with common_material/cv.toml. "
            f"Run `make cv` and commit the result."
        )
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return False
