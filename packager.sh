#!/bin/sh
# set -x
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

#  "submodule foreach" vars: $name, $path, $sha1 and $toplevel:
# git submodule foreach "git archive HEAD | (cd \"\${toplevel}/${GEM_BUILD_SRC}/\$path\" ; tar xv ) "


cd "$GEM_BUILD_SRC"

if [ $BUILD_DEVEL -eq 1 ]; then
    dt="$(date +%s)"
    hash="$(git log --pretty='format:%h' -1)"
    mv debian/changelog debian/changelog.orig
    h="$(head -n1 debian/changelog.orig)"
    pkg_name="$(echo "$h" | cut -d ' ' -f 1)"
    pkg_vers="$(echo "$h" | cut -d ' ' -f 2 | cut -d '(' -f 2 | cut -d ')' -f 1 )"
    pkg_rest="$(echo "$h" | cut -d ' ' -f 3-)"

    ( echo "$pkg_name (${pkg_vers}+dev${dt}-${hash}) $pkg_rest"
      echo
em openquake/bin/oqpath.py
      echo "  *  development version from $hash commit"
      echo
      echo " -- $DEBFULLNAME <$DEBEMAIL>  $(date -d@$dt -R)"
      echo
    )  > debian/changelog
    cat debian/changelog.orig >> debian/changelog
    rm debian/changelog.orig

#python-noq (0.2-4) precise; urgency=low
#
#  *  fix malformed patch
#
# -- Muharem Hrnjadovic <mh@foldr3.com>  Mon, 29 Oct 2012 15:14:15 +0100
#
    # $DEBEMAIL and $DEBFULLNAME
fi
# mods pre-packaging
mv LICENSE         openquake
mv README.txt      openquake/README
mv celeryconfig.py openquake
mv logging.cfg     openquake
mv openquake.cfg   openquake
mv bin/openquake   bin/noq
mv bin/openquake_supervisor bin/openquake_supervisor.py

rm bin/demo_risk.sh bin/demo_server.sh bin/openquake_messages_collector.py bin/openquake_supersupervisor bin/oqpath.py


rm -rf $(find demos -mindepth 1 -maxdepth 1 | egrep -v 'demos/simple_fault_demo_hazard|demos/event_based_hazard|demos/_site_model')
dpkg-buildpackage $DPBP_FLAG
cd -

# exit 0
#
# DEVEL
if [ -z "$GEM_SRC_PKG" ]; then
    echo "env var GEM_SRC_PKG not set, exit"
    exit 1
fi
GEM_BUILD_PKG="${GEM_SRC_PKG}/pkg"
mksafedir "$GEM_BUILD_PKG"
GEM_BUILD_EXTR="${GEM_SRC_PKG}/extr"
mksafedir "$GEM_BUILD_EXTR"
cp  ${GEM_BUILD_ROOT}/python-noq_*.deb  $GEM_BUILD_PKG
cd "$GEM_BUILD_EXTR"
dpkg -x $GEM_BUILD_PKG/python-noq_*.deb .
dpkg -e $GEM_BUILD_PKG/python-noq_*.deb 
