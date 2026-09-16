# LaTeX CV — Alberto Zancanaro

A standalone LaTeX project: it compiles on its own and can be imported into Overleaf without
anything else from this repository. Two variants share one source:

| File         | Output | Use for                                                                            |
| ------------ | ------ | ---------------------------------------------------------------------------------- |
| `main.tex`   | 1 page | Most applications. Publications reduced to three selected entries.                 |
| `cv_long.tex`| 2+     | Academic / research-institute applications where the full publication list matters. |

## Generated vs hand-written

This is the one thing to understand before editing anything here.

```
generated/    written by bin/cv/build_tex.py from common_material/cv.toml
              NEVER edit: the next `make cv` overwrites it, and CI rejects drift
sections/     hand-written prose — yours
zancanarocv.sty, main.tex, cv_long.tex   layout and drivers — hand-written
```

`generated/` holds the facts: contact details, education, experience, skills, languages,
projects, publications. `sections/` holds the writing:

- `summary.tex` — the profile paragraph. The highest-value edit for any application, and the
  main lever on the one-page budget. Keep it to three lines.
- `legal_it.tex` — the GDPR / D.Lgs. 445/2000 footer, off by default.
- `local_overrides.tex` — ships empty; an escape hatch for a genuine one-off.

## Compiling

**Overleaf** — works with the default pdfLaTeX compiler, no project settings to change.
LuaLaTeX also works. For the long version: _Menu → Main document → `cv_long.tex`_.

**Overleaf is a compile surface, not an edit surface.** This project is mirrored into
`jesus-333/cv_claude` one-way from `jesus-333.github.io`; anything you change in Overleaf is
overwritten on the next mirror. Real edits go to `common_material/cv.toml` (facts) or
`sections/summary.tex` (prose).

**Locally** — from the repository root:

```bash
make cv-pdf        # compile and publish to assets/pdf/Zancanaro_CV.pdf
make cv-pdf-long
```

or from this directory, `make`, `make long`, `make all`, `make lua`, `make clean`. You need
`pdflatex` plus the `lato` and `fontawesome5` packages (Debian: `texlive-fonts-extra`).

## Tailoring for a new application

1. **`sections/summary.tex`** — rewrite the profile paragraph for the role. Hand-written, and
   the only step that is genuinely authorship.
2. Everything else is selection and ordering, so it lives in `common_material/cv.toml` under
   `[profiles.<name>]`: `tagline`, which `experience` and `projects` to show and in what order,
   which three publications, and `skill_order`.

```bash
make cv PROFILE=industry_ml && make cv-pdf
git checkout cv_tex/generated        # back to the committed default
```

Copy the `[profiles.industry_ml]` block in `cv.toml` and retune it. A profile can only select
and reorder entries that already exist — referencing an id that does not exist is an error, not
a silent omission. Then check the output is still one page.

## Conventions worth knowing

- **`\cvTODO{...}` typesets in red.** Every unfilled placeholder uses it, so an unfinished CV
  cannot be sent by accident. In `cv.toml` these are written `@TODO{...}`, and they also block
  the website generators — see [`../common_material/README.md`](../common_material/README.md).
- **`\me`** expands to a bold _A. Zancanaro_; the publication generator inserts it automatically
  wherever your name appears in an author list.
- **Density.** `\usepackage[compact]{zancanarocv}` (what `main.tex` uses) tightens the vertical
  rhythm; `[relaxed]` (what `cv_long.tex` uses) gives more air. If a one-pager runs a line or two
  over, switch to `compact` before you start cutting content. All spacing derives from the
  lengths at the top of `zancanarocv.sty`.
- **Accent colour.** One definition, `cvaccent` in `zancanarocv.sty`, drives rules, icons and
  links. Set it to black for a strictly monochrome CV.
- **Icons are hidden from the text layer.** `\cvicon` wraps each glyph in an empty `ActualText`,
  so copy-paste and CV-parsing software read the contact details rather than stray glyphs.
- **Italian legal footer.** `sections/legal_it.tex` is off by default; uncomment the `\input`
  line at the bottom of a driver for Italian applications.

## Still to fill in

These are the `@TODO` markers in `common_material/cv.toml`, and they are why `make cv` needs
`ALLOW_TODO=1` today:

- **Current position** — the CV stops at the doctorate in 01/2025.
- **LinkedIn handle** and, if you want it listed, a personal website.
- **Location** — city and country.
- **Spoken language levels** (CEFR).
