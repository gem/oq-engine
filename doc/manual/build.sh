#!/bin/bash

if [ $GEM_SET_DEBUG ]; then
    set -x
fi

inkscape -A figures/oq_manual_cover.pdf figures/oq_manual_cover.svg

pdflatex -shell-escape -interaction=nonstopmode oq-manual.tex &> log.md
bibtex oq-manual > log.md
pdflatex -shell-escape -interaction=nonstopmode oq-manual.tex &> log.md
pdflatex -shell-escape -interaction=nonstopmode oq-manual.tex &> log.md
makeindex oq-manual.idx
makeglossaries oq-manual &> log.md
pdflatex -shell-escape -interaction=nonstopmode oq-manual.tex &> log.md
cat log.md | egrep "Error|Warning"
./clean.sh
if [ "$1" == "--compress" ]; then
    pdfinfo "oq-manual.pdf" | sed -e 's/^ *//;s/ *$//;s/ \{1,\}/ /g' -e 's/^/  \//' -e '/CreationDate/,$d' -e 's/$/)/' -e 's/: / (/' > .pdfmarks
    sed -i '1s/^ /[/' .pdfmarks
    sed -i '/:)$/d' .pdfmarks
    echo "  /DOCINFO pdfmark" >> .pdfmarks

    gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=compressed-oq-manual.pdf oq-manual.pdf .pdfmarks

    mv -f compressed-oq-manual.pdf oq-manual.pdf
fi
