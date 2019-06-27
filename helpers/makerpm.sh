#!/bin/bash
#
# makerpm.sh  Copyright (C) 2015-2019 GEM Foundation
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

set -e

checkcmd() {
    command -v $1 >/dev/null 2>&1 || { echo >&2 "This script requires '$1' but it isn't available. Aborting."; exit 1; }
}

CUR=$(pwd)
BASE=$(cd $(dirname $0)/.. && /bin/pwd)

REPO=oq-engine
BRANCH='HEAD'
STABLE=0
EXTRA=''

while getopts "r:lc" opt; do
    case ${opt} in
        \?)
            echo "Usage: $0 [-c] [-l] [-r N] [BRANCH]"
            echo -e "\\nOptions:\\n\\t-l: build RPM locally\\n\\t-c: clean build dir before starting a new build\\n\\t-r N: make a stable release"
            exit 0
            ;;
        r)
            STABLE=1
            if ! [[ $OPTARG =~ ^[0-9]+$ ]] ; then
               echo "Error: please provide a valid PKG number" >&2; exit 1
            fi
            PKG="$OPTARG"
            ;;
        l)
            BUILD=1
            ;;
        c)
            CLEAN=1
            ;;
    esac
done
shift $((OPTIND -1))
if [ "$1" ]; then
    BRANCH="$1";
fi

if [ "$CLEAN" == "1" ]; then
    rm -Rf $BASE/build-rpm
    echo "$BASE/build-rpm cleaned"
fi

cd $BASE
mkdir -p build-rpm/{RPMS,SOURCES,SPECS,SRPMS}

LIB=$(cut -d "-" -f 2 <<< $REPO)
SHA=$(git rev-parse --short $BRANCH)
VER=$(cat openquake/baselib/__init__.py | sed -n "s/^__version__[  ]*=[    ]*['\"]\([^'\"]\+\)['\"].*/\1/gp")
TIME=$(date +"%s")
echo "$LIB - $BRANCH - $SHA - $VER"

sed "s/##_stable_##/${STABLE}/g;s/##_repo_##/${REPO}/g;s/##_version_##/${VER}/g;s/##_timestamp_##/${TIME}/g" rpm/python3-${REPO}.spec.inc > build-rpm/SPECS/python3-${REPO}.spec

if [ "$STABLE" == "1" ]; then
    git archive --format=tar --prefix=${REPO}-${VER}/ $BRANCH | gzip -9 > build-rpm/SOURCES/${REPO}-${VER}.tar.gz
    sed -i "s/##_release_##/${PKG}/g" build-rpm/SPECS/python3-${REPO}.spec
    OUT=python3-${REPO}-${VER}-${PKG}.src.rpm
else
    git archive --format=tar --prefix=${REPO}-${VER}-git${SHA}/ $BRANCH | gzip -9 > build-rpm/SOURCES/${REPO}-${VER}-git${SHA}.tar.gz
    sed -i "s/##_release_##/git${SHA}/g" build-rpm/SPECS/python3-${REPO}.spec
    OUT=python3-${REPO}-${VER}-${TIME}_git${SHA}.src.rpm
fi
cp debian/patches/openquake.cfg.patch build-rpm/SOURCES

mock -r openquake --buildsrpm --spec build-rpm/SPECS/python3-${REPO}.spec --source build-rpm/SOURCES --resultdir=build-rpm/SRPMS/
if [ "$BUILD" == "1" ]; then
    mock -r openquake build-rpm/SRPMS/${OUT} --resultdir=build-rpm/RPMS $EXTRA
fi

cd $CUR
