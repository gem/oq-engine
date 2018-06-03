#!/bin/bash

if [ $GEM_SET_DEBUG ]; then
    set -x
fi
set -e

CURPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VERSION="$(cat $CURPATH/../../openquake/baselib/__init__.py | sed -n "s/^__version__[  ]*=[    ]*['\"]\([^'\"]\+\)['\"].*/\1/gp")"
cd $CURPATH
sed -i "s/Version X\.Y\.Z/Version $VERSION/" figures/oq_manual_cover.svg

inkscape -A figures/oq_manual_cover.pdf figures/oq_manual_cover.svg

sed -i "s/#PUBYEAR#/$(date +%Y)/g; s/#PUBMONTH#/$(date +%B)/g" oq-manual.tex
sed -i "s/version X\.Y\.Z/version $VERSION/; s/ENGINE\.X\.Y\.Z/ENGINE\.$VERSION/" oq-manual.tex

(pdflatex -halt-on-error -shell-escape -interaction=nonstopmode oq-manual.tex
bibtex oq-manual
pdflatex -halt-on-error -shell-escape -interaction=nonstopmode oq-manual.tex
makeindex oq-manual.idx
makeglossaries oq-manual
pdflatex -halt-on-error -shell-escape -interaction=nonstopmode oq-manual.tex
makeglossaries oq-manual) | tee -a full_log.log | egrep -i "error|warning|missing"

echo -e "\n\n=== FINAL RUN ===\n\n"
pdflatex -halt-on-error -shell-escape -interaction=nonstopmode oq-manual.tex | tee -a full_log.log | egrep -i "error|warning|missing"

if [ -f oq-manual.pdf ]; then
    ./clean.sh || true
    if [ "$1" == "--compress" ]; then
        pdfinfo "oq-manual.pdf" | sed -e 's/^ *//;s/ *$//;s/ \{1,\}/ /g' -e 's/^/  \//' -e '/CreationDate/,$d' -e 's/$/)/' -e 's/: / (/' > .pdfmarks
        sed -i '1s/^ /[/' .pdfmarks
        sed -i '/:)$/d' .pdfmarks
        echo "  /DOCINFO pdfmark" >> .pdfmarks

        gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=compressed-oq-manual.pdf oq-manual.pdf .pdfmarks

        mv -f compressed-oq-manual.pdf oq-manual.pdf
    fi
else
    exit 1
fi
