#!/bin/sh
# set -x
set -e
GEM_BUILD_ROOT="build-deb"
GEM_BUILD_SRC="${GEM_BUILD_ROOT}/python-oq"

GEM_ALWAYS_YES=false

mksafedir () {
    local dname

    dname="$1"
    if [ "$GEM_ALWAYS_YES" != "true" -a -d "$dname" ]; then
        echo "$dname already exists"
        echo "press Enter to continue or CTRL+C to abort"
        read a
    fi
    rm -rf $dname
    mkdir -p $dname
}

usage () {
    local ret

    ret=$1

    echo
    echo "USAGE:"
    echo "    $0 [-D|--development] [-B|--binaries] build debian source package."
    echo "       if -B argument is present binary package is build too."
    echo "       if -D argument is present a package with self-computed version is produced."
    echo
    exit $ret
}

#
#  MAIN

BUILD_BINARIES=0
BUILD_DEVEL=0
#  args management
while [ $# -gt 0 ]; do
    case $1 in
        -D|--development)
            BUILD_DEVEL=1
            ;;
        -B|--binaries)
            BUILD_BINARIES=1
            ;;
        -h|--help)
            usage 0
            break
            ;;
        *)
            usage 1
            break
            ;;
    esac
    shift
done

DPBP_FLAG=""
if [ "$BUILD_BINARIES" -eq 0 ]; then
    DPBP_FLAG="-S"
fi

mksafedir "$GEM_BUILD_ROOT"

mksafedir "$GEM_BUILD_SRC"

git archive HEAD | (cd "$GEM_BUILD_SRC" ; tar xv)

# git submodule init
# git submodule update
##  "submodule foreach" vars: $name, $path, $sha1 and $toplevel:
# git submodule foreach "git archive HEAD | (cd \"\${toplevel}/${GEM_BUILD_SRC}/\$path\" ; tar xv ) "


cd "$GEM_BUILD_SRC"

# date
dt="$(date +%s)"

# version from setup.py
stp_vers="$(cat setup.py | grep '^[ 	]*version=' | sed 's/^[ 	]*version="//g;s/".*//g')"
stp_maj="$(echo "$stp_vers" | sed 's/\..*//g')"
stp_min="$(echo "$stp_vers" | sed 's/^[^\.]*\.\([^\.]*\).*/\1/g')"

# version info from openquake/__init__.py
ini_maj="$(cat openquake/__init__.py | grep '# major' | sed 's/^[ ]*//g;s/,.*//g')"
ini_min="$(cat openquake/__init__.py | grep '# minor' | sed 's/^[ ]*//g;s/,.*//g')"
ini_spn="$(cat openquake/__init__.py | grep '# sprint number' | sed 's/^[ ]*//g;s/,.*//g')"

# version info from debian/changelog
h="$(head -n1 debian/changelog)"
pkg_vers="$(echo "$h" | cut -d ' ' -f 2 | cut -d '(' -f 2 | cut -d ')' -f 1 | sed 's/[-+].*//g')"
pkg_maj="$(echo "$pkg_vers" | sed 's/\..*//g')"
pkg_min="$(echo "$pkg_vers" | sed 's/^[^\.]*\.\([^\.]*\).*/\1/g')"

if [  "$ini_maj" != "$pkg_maj" -o "$ini_maj" != "$stp_maj" -o \
      "$ini_min" != "$pkg_min" -o "$ini_min" != "$stp_min" ]; then
    echo 
    echo "Versions are not aligned"
    echo "    init:  ${ini_maj}.${ini_min}"
    echo "    setup: ${stp_maj}.${stp_min}"
    echo "    pkg:   ${pkg_maj}.${pkg_min}"
    echo
    echo "press [enter] to continue, [ctrl+c] to abort"
    read a
fi

sed -i "s/^\([ 	]*\)[^)]*\()  # release date .*\)/\1${dt}\2/g" openquake/__init__.py

if [ $BUILD_DEVEL -eq 1 ]; then
    hash="$(git log --pretty='format:%h' -1)"
    mv debian/changelog debian/changelog.orig
    h="$(head -n1 debian/changelog.orig)"
    pkg_name="$(echo "$h" | cut -d ' ' -f 1)"
    pkg_vers="$(echo "$h" | cut -d ' ' -f 2 | cut -d '(' -f 2 | cut -d ')' -f 1)"    
    pkg_vsuf="$(echo "$pkg_vers" | sed 's/^[0-9\.\-]*//g')"
    pkg_vrst="$(echo "$pkg_vers" | sed 's/+.*$//g')"
    pkg_vdeb="$(echo "$pkg_vrst" | sed 's/^[0-9\.]*//g')"
    pkg_vrst="$(echo "$pkg_vrst" | sed 's/-.*$//g')"
    pkg_vbfx="$(echo "$pkg_vrst" | sed 's/^.*\.//g')"
    pkg_vrst="$(echo "$pkg_vrst" | sed 's/.[0-9]*$//g')"
    
    pkg_rest="$(echo "$h" | cut -d ' ' -f 3-)"

    ( echo "$pkg_name (${pkg_vrst}.${pkg_vbfx}${pkg_vdeb}+dev${dt}-${hash}) $pkg_rest"
      echo
      echo "  *  development version from $hash commit"
      echo
      echo " -- $DEBFULLNAME <$DEBEMAIL>  $(date -d@$dt -R)"
      echo
    )  > debian/changelog
    cat debian/changelog.orig >> debian/changelog
    rm debian/changelog.orig
fi
# mods pre-packaging
mv LICENSE         openquake
mv README.txt      openquake/README
mv celeryconfig.py openquake
mv openquake.cfg   openquake

mv bin/openquake   bin/oqscript.py
mv bin             openquake/bin

rm -rf $(find demos -mindepth 1 -maxdepth 1 | egrep -v 'demos/simple_fault_demo_hazard|demos/event_based_hazard|demos/_site_model')
dpkg-buildpackage $DPBP_FLAG
cd -

if [ $BUILD_DEVEL -ne 1 ]; then
    exit 0
fi

#
# DEVEL EXTRACTION OF SOURCES
if [ -z "$GEM_SRC_PKG" ]; then
    echo "env var GEM_SRC_PKG not set, exit"
    exit 0
fi
GEM_BUILD_PKG="${GEM_SRC_PKG}/pkg"
mksafedir "$GEM_BUILD_PKG"
GEM_BUILD_EXTR="${GEM_SRC_PKG}/extr"
mksafedir "$GEM_BUILD_EXTR"
cp  ${GEM_BUILD_ROOT}/python-oq_*.deb  $GEM_BUILD_PKG
cd "$GEM_BUILD_EXTR"
dpkg -x $GEM_BUILD_PKG/python-oq_*.deb .
dpkg -e $GEM_BUILD_PKG/python-oq_*.deb
