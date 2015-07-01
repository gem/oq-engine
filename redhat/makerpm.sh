#!/bin/bash
#
# makerpm.sh  Copyright (c) 2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>

# Work in progress

set -e

BASE=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)/builddir
rm -Rf $BASE

REPO=oq-hazardlib

if [ -n "$1" ];
then
    BRANCH="$1"
else
    BRANCH='master'
fi
echo $BRANCH
mkdir -p $BASE/{RPMS,SOURCES,SPECS,SRPMS}

cd $BASE/SOURCES
if [ ! -d $REPO ]; then
    git clone --depth=1 -b $BRANCH https://github.com/gem/${REPO}.git
    cd $REPO
else
    cd $REPO
    git fetch
    git reset --hard HEAD
    git checkout $BRANCH
    git pull
fi

LIB=$(cut -d "-" -f 2 <<< $REPO)
SHA=$(git rev-parse --short HEAD)
VER=$(cat openquake/${LIB}/__init__.py | sed -n "s/^__version__[  ]*=[    ]*['\"]\([^'\"]\+\)['\"].*/\1/gp")

sed "s/##_repo_##/${REPO}/g;s/##_version_##/${VER}/g;s/##_release_##/git${SHA}/g" redhat/python-${REPO}.spec > $BASE/SPECS/python-${REPO}.spec

git archive --format=tar --prefix=${REPO}-${VER}-git${SHA}/ $BRANCH | pigz > ../${REPO}-${VER}-git${SHA}.tar.gz
cd ..

mock -r openquake --buildsrpm --spec $BASE/SPECS/python-${REPO}.spec --source $BASE/SOURCES --resultdir=$BASE/SRPMS/
mock -r openquake $BASE/SRPMS/python-${REPO}-${VER}-git${SHA}.src.rpm --resultdir=$BASE/RPMS
