# Local builds. Overleaf ignores this file.
#   make            one-page CV
#   make long       extended CV
#   make all        both
#   make lua        one-page CV via LuaLaTeX
#   make clean      remove build artefacts

LATEX ?= pdflatex
FLAGS  = -interaction=nonstopmode -halt-on-error

.PHONY: all one long lua clean

one: main.pdf
all: one long

DEPS = zancanarocv.sty $(wildcard generated/*.tex) $(wildcard sections/*.tex)

main.pdf: main.tex $(DEPS)
	$(LATEX) $(FLAGS) main.tex
	$(LATEX) $(FLAGS) main.tex

long: cv_long.tex $(DEPS)
	$(LATEX) $(FLAGS) cv_long.tex
	$(LATEX) $(FLAGS) cv_long.tex

lua:
	$(MAKE) LATEX=lualatex one

clean:
	rm -f *.aux *.log *.out *.fls *.fdb_latexmk *.synctex.gz *.toc *.xdv
