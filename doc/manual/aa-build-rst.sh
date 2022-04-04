#!/bin/bash
PANDOC=/home/pslh/local/pandoc-2.17.1.1/bin/pandoc

if [ $GEM_SET_DEBUG ]; then
    set -x
fi
set -e

CURPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VERSION="$(cat $CURPATH/../../openquake/baselib/__init__.py | \
	sed -n "s/^__version__[  ]*=[    ]*['\"]\([^'\"]\+\)['\"].*/\1/gp")"
cd $CURPATH
sed -i "s/Version X\.Y\.Z/Version $VERSION/" figures/oq_manual_cover.svg

inkscape -A figures/oq_manual_cover.pdf figures/oq_manual_cover.svg

sed -i "s/#PUBYEAR#/$(date +%Y)/g; s/#PUBMONTH#/$(date +%B)/g" oq-manual.tex
sed -i "s/version X\.Y\.Z/version $VERSION/; s/ENGINE\.X\.Y\.Z/ENGINE\.$VERSION/" oq-manual.tex

#$PANDOC -t rst -o oq-manual-fix-acr.rst oq-manual.tex
#sed -f acronyms.sed oq-manual-fix-acr.rst > oq-manual.rst
$PANDOC -s -t rst -N --number-offset=-1 --toc --citeproc oq-manual.tex | \
	sed -f acronyms.sed  > oq-manual-unfixed.rst

./fix-rst-sections.py  oq-manual-unfixed.rst > oq-manual-gen.rst

# build HTML from RST
#$PANDOC -t html --section-divs --toc -o oq-manual-ph.html oq-manual.rst
#$PANDOC -s -t html -N --number-offset=-1 --toc -o oq-manual-ph.html oq-manual.rst
$PANDOC -s -t html -N --number-offset=0 --shift-heading-level-by -1 --toc -o oq-manual-gen.html oq-manual-gen.rst

exit 0
