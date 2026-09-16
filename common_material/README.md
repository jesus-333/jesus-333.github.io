# common_material

The canonical inputs shared by the website and the LaTeX CV. Two files, both hand-edited:

| File         | What it is                                                                                                            |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| `cv.toml`    | Every CV fact: name, contacts, education, experience, skills, languages, projects, and which publications to feature. |
| `papers.bib` | The publication records themselves, in BibTeX.                                                                        |

Everything else is generated from these two.

## Data flow

```
common_material/cv.toml ──┬──> _data/cv.yml              the website's /cv/ page
                          ├──> assets/json/resume.json   JSON Resume twin
                          └──> cv_tex/generated/*.tex    the LaTeX CV
common_material/papers.bib ─┬──> _bibliography/papers.bib  jekyll-scholar, /publications/
                            └──> cv_tex/generated/papers.bib
```

Nothing flows the other way. Editing a generated file is always the wrong move: the next
`make cv` overwrites it, and CI fails the push before then.

## Commands

```bash
make cv           # regenerate everything
make cv-check     # verify the generated files match the source (CI runs this)
make cv-pdf       # compile the LaTeX CV -> assets/pdf/Zancanaro_CV.pdf
```

Tailoring for one application:

```bash
make cv PROFILE=industry_ml && make cv-pdf
git checkout cv_tex/generated        # back to the committed default
```

## The two conventions in cv.toml

**`<field>_tex`** — an optional sibling of any string field. Present, it is emitted verbatim
into LaTeX while the plain field still feeds the website. Use it when you want real LaTeX
markup: `\textbar{}`, `\textsuperscript{11}C`, `\emph{}`. The generator checks the braces
balance, so a broken opt-out is caught when you generate rather than when you compile.

**`@TODO{...}`** — a placeholder. In the PDF it becomes `\cvTODO{...}` and typesets in red.
The two website generators **refuse to run** while one is present, unless you pass
`--allow-todo` (`make cv ALLOW_TODO=1`). An entry-level `todo = true` marks a whole entry:
red in the PDF, dropped from the website entirely.

This is why `make cv` fails on a fresh clone today — `cv.toml` still carries placeholders for
your location, LinkedIn handle, CEFR language levels and current position. That is the gate
working, not a broken script. Fill them in and the flag stops being needed.

## Publications

`papers.bib` is the record store. `cv.toml` never duplicates a title or an author list; its
`[publications]` table only says which entries to feature on the one-page CV, which to exclude,
and how to correct a misfiled one:

```toml
[publications]
exclude  = ["zancanaro2025modeling"]        # the PhD thesis; already under Education
featured = ["cisotto2024hveegnet", "..."]   # the three on the one-page CV

[publications.overrides.cisotto2023hveegnet]
class = "preprint"                          # journal | conference | preprint | thesis
```

A key in `exclude`, `featured` or `overrides` that names no BibTeX entry is a hard error —
otherwise a renamed key would silently drop a paper.

`sync_bib.py` also refuses to run on a duplicate citation key. That is not hypothetical: this
bibliography shipped `zancanaro2023veegnet` twice, on two different papers, so one of them was
invisible on the site. It is now `zancanaro2023veegnet_springer`.

## Mirroring to cv_claude (Overleaf)

`.github/workflows/cv-mirror.yml` pushes `cv_tex/` to the standalone `jesus-333/cv_claude`
repo whenever `cv_tex/**` changes on `main`, so the CV can be opened in Overleaf.

**The mirror is one-way and destructive on the far side.** Anything you edit in Overleaf is
overwritten on the next run. Treat Overleaf as a place to compile the CV, not to edit it.

It needs a token, once:

1. Create a fine-grained PAT at <https://github.com/settings/personal-access-tokens/new>
   - Repository access: only `jesus-333/cv_claude`
   - Repository permissions: **Contents → Read and write**
2. Add it here as a repository secret named `CV_SYNC_TOKEN`
   (Settings → Secrets and variables → Actions → New repository secret)

Until that secret exists the workflow fails with a message saying so, rather than
half-mirroring.
