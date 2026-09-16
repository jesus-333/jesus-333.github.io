# CV pipeline. Everything here is manual: nothing in this file runs
# automatically on push, and none of it is part of the Jekyll build.
#
#   make cv         regenerate every derived CV file from common_material/
#   make cv-check   verify the derived files match the source (what CI runs)
#   make cv-pdf     compile the LaTeX CV and publish the PDF to assets/pdf/
#
# Tailor for one application:
#   make cv PROFILE=industry_ml && make cv-pdf
#   git checkout cv_tex/generated        # back to the committed default
#
# `--allow-todo` is NOT passed by default. While common_material/cv.toml
# still holds @TODO placeholders, `make cv` stops before writing anything
# to the public website and tells you which ones. That is deliberate: it
# is the only thing standing between a placeholder and a published page.
# Use `make cv ALLOW_TODO=1` if you knowingly want to publish them.

PYTHON ?= python3
PROFILE ?= default
ALLOW_TODO ?=
TODO_FLAG = $(if $(ALLOW_TODO),--allow-todo,)

.PHONY: cv cv-check cv-pdf cv-pdf-long

cv:
	$(PYTHON) bin/cv/sync_bib.py
	$(PYTHON) bin/cv/build_cv_yml.py $(TODO_FLAG)
	$(PYTHON) bin/cv/build_resume_json.py $(TODO_FLAG)
	$(PYTHON) bin/cv/build_tex.py --profile $(PROFILE)
	$(PYTHON) bin/cv/scrape_projects.py

cv-check:
	$(PYTHON) bin/cv/sync_bib.py --check
	$(PYTHON) bin/cv/build_cv_yml.py --check $(TODO_FLAG)
	$(PYTHON) bin/cv/build_resume_json.py --check $(TODO_FLAG)
	$(PYTHON) bin/cv/build_tex.py --check --profile $(PROFILE)
	$(PYTHON) bin/cv/scrape_projects.py --check

cv-pdf:
	bash bin/cv/build_pdf.sh $(if $(filter-out default,$(PROFILE)),--profile $(PROFILE),)

cv-pdf-long:
	bash bin/cv/build_pdf.sh --long
