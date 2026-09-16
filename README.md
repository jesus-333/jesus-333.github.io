# Personal website and CV

Constructed from [al-folio](https://github.com/alshedivat/al-folio/).

This repository holds two things that used to be two repositories: the Jekyll website published
at <https://jesus-333.github.io>, and the LaTeX CV. They share one source of truth, so the CV on
the website and the CV in the PDF cannot drift apart.

## Layout

| Path               | What it is                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------- |
| `common_material/` | **Canonical.** `cv.toml` (every CV fact) and `papers.bib` (every publication). Hand-edited. |
| `cv_tex/`          | The LaTeX CV. A standalone project — importable into Overleaf on its own.                   |
| `bin/cv/`          | The generators. Manual; nothing here runs automatically.                                    |
| everything else    | The al-folio Jekyll site, in the layout the template expects.                               |

```
common_material/cv.toml ──┬──> _data/cv.yml              the website's /cv/ page
                          ├──> assets/json/resume.json
                          └──> cv_tex/generated/*.tex    the LaTeX CV
common_material/papers.bib ─┬──> _bibliography/papers.bib  /publications/
                            └──> cv_tex/generated/papers.bib
```

Files on the right-hand side are generated and carry a "do not edit" banner. CI fails any push
where they have drifted from the source.

## Common tasks

```bash
make cv                      # regenerate the derived CV files after editing cv.toml
make cv-pdf                  # compile the LaTeX CV -> assets/pdf/Zancanaro_CV.pdf
make cv PROFILE=industry_ml  # a CV tailored for one application

bundle exec jekyll serve     # preview the site at http://localhost:4000/
```

`make cv` deliberately refuses to run while `cv.toml` still holds `@TODO` placeholders, so one
cannot reach a public page by accident. Use `make cv ALLOW_TODO=1` while the CV is unfinished.

Details: [`common_material/README.md`](common_material/README.md) for the data flow and the
Overleaf mirror, [`cv_tex/README.md`](cv_tex/README.md) for compiling and tailoring the PDF.
