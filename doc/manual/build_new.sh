#!/bin/bash
pdflatex -shell-escape -interaction=nonstopmode oq-manual.tex
bibtex oq-manual
pdflatex -shell-escape -interaction=nonstopmode oq-manual.tex
makeindex oq-manual.idx
makeglossaries oq-manual
pdflatex -shell-escape -interaction=nonstopmode oq-manual.tex

