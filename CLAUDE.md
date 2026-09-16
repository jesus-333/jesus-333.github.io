# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

`AGENTS.md` (imported above) is the **authoritative** agent entry point: change routing, the stop sign for gem-owned paths, the four silent failure modes, and the validated command set. Keep it short and ecosystem-neutral. Cross-repo architecture — the wrapper/tag/gem delegation table, feature gating, the v1 config contract, local overrides — lives in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); area-to-gem ownership lives in [`docs/BOUNDARIES.md`](docs/BOUNDARIES.md).

**Read those three before editing anything.** Everything below is Claude-specific or longer-form operational detail that does not belong in the short entry point. Do not restate facts from those files here — link to them.

## Daily dev loop

```bash
bundle install                                # ruby gems
bundle exec jekyll serve                      # dev server → http://localhost:4000/ (this fork's baseurl is /)
bundle exec jekyll build                      # production-style build to _site/
bash test/integration_distill.sh              # run ONE integration test (any of the seven in test/)
npm run test:visual:update                    # refresh playwright snapshots after intentional UI change
bundle exec al-folio upgrade apply --safe     # deterministic codemods (font-weight-* → font-*, remote→local URLs)
bundle exec al-folio upgrade overrides diff <path>    # then `overrides accept <path>` to acknowledge an override

make cv                                       # regenerate every derived CV file
make cv-check ALLOW_TODO=1                    # verify they match common_material/ (CI gate)
make cv-pdf                                   # compile cv_tex → assets/pdf/Zancanaro_CV.pdf
```

## The CV pipeline

`common_material/cv.toml` is the single source of truth for every CV fact, and
`common_material/papers.bib` for every publication record. `bin/cv/*` generates `_data/cv.yml`
(what `/cv/` renders), `assets/json/resume.json`, `_bibliography/papers.bib` and
`cv_tex/generated/*.tex` from them. Never edit a generated file — see
[`common_material/README.md`](common_material/README.md) for the data flow, the `@TODO` gate that
stops placeholders reaching a public page, and the `[profiles.*]` mechanism for tailoring the
PDF per application. The upstream RenderCV/Typst pipeline was removed; LaTeX is the only PDF
generator.

## Optional toolchains

- **Jupyter posts.** `bin/setup-python-deps` installs _only_ `jupyter` and `nbconvert` (via `pip --user --break-system-packages`) for `jekyll-jupyter-notebook`. It does **not** read `requirements.txt`. Missing `jupyter-nbconvert` is warn-and-continue; notebook rendering is skipped.
- **Everything else Python.** [`requirements.txt`](requirements.txt) is the fuller list and must be installed separately (`python3 -m pip install -r requirements.txt`): `scholarly` for `bin/update_scholar_citations.py`, plus `nbconvert` and `pyyaml`. `pyyaml` is also what `bin/cv/*` needs. `rendercv[full]` was dropped with the Typst pipeline.
- **Responsive images.** `imagemagick.enabled: true` needs ImageMagick `convert` on `PATH`.
- **Manual deploy.** `bin/deploy` is the manual `gh-pages` build + purgecss + force-push path; CI normally deploys. `purgecss` is not a devDependency — install it with `npm install -g purgecss`.

## Docker serving model (v1-specific)

`docker compose up -d` bind-mounts the repo to `/srv/jekyll` and runs `bin/entry_point.sh`, which serves with `--force_polling --destination /tmp/_site`. The build output deliberately goes to **container-local `/tmp/_site`, not the bind-mounted `_site`** — writing `_site` back across the host bind mount caused write deadlocks. The container also `inotifywait`s `_config.yml` and restarts Jekyll on change (config edits aren't hot-reloaded by `--watch`). Verify with the `/al-folio` baseurl: `curl -fsS http://127.0.0.1:8080/al-folio/`. `docker-compose-slim.yml` pulls a prebuilt `:slim` image instead of building locally.

Note the Docker section above describes upstream's `/al-folio` baseurl; this fork serves at `/`,
so verify with `curl -fsS http://127.0.0.1:8080/`.

## CI gates and the style contract

`npm run lint:style-contract` (`test/style_contract.js`) is the automated enforcement of the thin-starter boundary and will fail CI if you cross it. Beyond the forbidden paths listed in `AGENTS.md`, it also asserts that `_config.yml` keeps `theme: al_folio_core` and the required plugins, that the `third_party_libraries` SRI pins are present, and that the `al_math` Gemfile pin stays on a released version rather than a git branch.

Other gates:

- `unit-tests.yml` — style contract, `make cv-check` (generated CV files vs `common_material/`), plus all seven `test/integration_*.sh` scripts (`comments`, `plugin_toggles`, `distill`, `bootstrap_compat`, `upgrade_cli`, `css_minify`, `new_plugins`).
- `visual-regression.yml` — Playwright on chromium + webkit, diffing against a `v0.16.3` baseline worktree. **Disabled in this fork**: it needs the `v0.16.3` tag, which only exists upstream, so `git worktree add` failed on every PR. Guarded with the same `github.repository` check the other upstream-only workflows use.
- `upgrade-check.yml` — `bundle exec al-folio upgrade audit`.
- `prettier.yml` — Prettier with `@shopify/prettier-plugin-liquid` and `printWidth: 150`. Run `npm run lint:prettier` before pushing; `npx prettier . --write` fixes.
- `cv-mirror.yml` — one-way mirror of `cv_tex/` into `jesus-333/cv_claude` for Overleaf, on `cv_tex/**` changes. Needs the `CV_SYNC_TOKEN` secret; destructive on the far side.
- `cv-sync.yml` — `workflow_dispatch` only; runs `make cv` and commits the result with a scoped `git add`.
- `update-tocs.yml` — regenerates `<!--ts-->…<!--te-->` blocks in changed root and `docs/` Markdown files. If you add or rename a heading, expect a follow-up auto-commit on `main`.

## Gem version pins

`Gemfile` pins every `al-*` gem to an exact released version in `group :al_folio_plugins`, and `_config.yml` lists the same gems under `plugins:`. Read the current pins from the `Gemfile` rather than trusting any version quoted in prose — including here. To test a gem fix against this site, repoint the `Gemfile` at a sibling checkout (`path:`, `git:`, or `branch:`) and `bundle install`; see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#working-on-a-gem-alongside-the-starter). Revert the pin before committing.
