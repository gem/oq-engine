#!/bin/bash
# export PS4='+${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]}: '
# set -x
set -e
GEM_DEB_PACKAGE="python-oq-engine"
GEM_DEB_SERIE="master"
if [ -z "$GEM_DEB_REPO" ]; then
    GEM_DEB_REPO="$HOME/gem_ubuntu_repo"
fi
GEM_BUILD_ROOT="build-deb"
GEM_BUILD_SRC="${GEM_BUILD_ROOT}/${GEM_DEB_PACKAGE}"

GEM_ALWAYS_YES=false

NL="
"
TB="	"

#
#  functions
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
    echo "    $0 [-D|--development] [-B|--binaries] [-U|--unsigned] [-R|--repository]    build debian source package."
    echo "       if -B is present binary package is build too."
    echo "       if -R is present update the local repository to the new current package"
    echo "       if -D is present a package with self-computed version is produced."
    echo "       if -U is present no sign are perfomed using gpg key related to the mantainer."
    echo "    $0 pkgtest <last-ip-digit>                  run tests into an ubuntu lxc environment"
    echo
    exit $ret
}

_pkgtest_innervm_run () {
    local haddr="$1"

    trap 'local LASTERR="$?" ; trap ERR ; (exit $LASTERR) ; return' ERR

    ssh $haddr "sudo apt-get update"
    ssh $haddr "sudo apt-get -y upgrade"
    gpg -a --export | ssh $haddr "sudo apt-key add -"
    # install package to manage repository properly
    ssh $haddr "sudo apt-get install -y python-software-properties"

    # create a remote "local repo" where place $GEM_DEB_PACKAGE package
    ssh $haddr mkdir -p repo/${GEM_DEB_PACKAGE}
    scp build-deb/${GEM_DEB_PACKAGE}_*.deb build-deb/${GEM_DEB_PACKAGE}_*.changes \
        build-deb/${GEM_DEB_PACKAGE}_*.dsc build-deb/${GEM_DEB_PACKAGE}_*.tar.gz \
        build-deb/Packages* build-deb/Sources*  build-deb/Release* $haddr:repo/${GEM_DEB_PACKAGE}
    ssh $haddr "sudo apt-add-repository \"deb file:/home/ubuntu/repo/${GEM_DEB_PACKAGE} ./\""
    #
    #  dependencies repos

    # python-oq-nrmllib
    scp -r ${GEM_DEB_REPO}/${GEM_DEB_SERIE}/python-oq-nrmllib $haddr:repo/
    ssh $haddr "sudo apt-add-repository \"deb file:/home/ubuntu/repo/python-oq-nrmllib ./\""

    # python-oq-hazardlib
    scp -r ${GEM_DEB_REPO}/${GEM_DEB_SERIE}/python-oq-hazardlib $haddr:repo/
    ssh $haddr "sudo apt-add-repository \"deb file:/home/ubuntu/repo/python-oq-hazardlib ./\""

    # python-oq-risklib
    scp -r ${GEM_DEB_REPO}/${GEM_DEB_SERIE}/python-oq-risklib $haddr:repo/
    ssh $haddr "sudo apt-add-repository \"deb file:/home/ubuntu/repo/python-oq-risklib ./\""

    ssh $haddr "sudo apt-get update"

    # packaging related tests (install, remove, purge, install, reinstall)
    ssh $haddr "sudo apt-get install -y ${GEM_DEB_PACKAGE}"
    ssh $haddr "sudo apt-get remove -y ${GEM_DEB_PACKAGE}"
    ssh $haddr "sudo apt-get install -y ${GEM_DEB_PACKAGE}"
    ssh $haddr "sudo apt-get install --reinstall -y ${GEM_DEB_PACKAGE}"

    # configure the machine to run tests
    ssh $haddr "echo \"local	all		\$USER		trust\" | sudo tee -a /etc/postgresql/9.1/main/pg_hba.conf"
    ssh $haddr "sudo sed -i 's/#standard_conforming_strings = on/standard_conforming_strings = off/g' /etc/postgresql/9.1/main/postgresql.conf"

    ssh $haddr "sudo service postgresql restart"
    ssh $haddr "sudo -u postgres  createuser -d -e -i -l -s -w \$USER"
    ssh $haddr "oq_create_db --yes --db-user=\$USER --db-name=openquake --no-tab-spaces --schema-path=/usr/share/pyshared/openquake/engine/db/schema"

    # run celeryd daemon
    ssh $haddr "cd /usr/openquake/engine ; celeryd >/tmp/celeryd.log 2>&1 3>&1 &"

    # copy demos file to $HOME
    ssh $haddr "cp -a /usr/share/doc/${GEM_DEB_PACKAGE}/examples/demos ."

    # run all of the hazard demos
    ssh $haddr "cd demos
    for ini in \$(find ./hazard -name job.ini); do
        DJANGO_SETTINGS_MODULE=openquake.engine.settings openquake --run-hazard  \$ini --exports xml
    done"

    trap ERR

    return
}

pkgtest_run () {
    local i e le_addr="$1" haddr

    #
    #  run build of package
    if [ -d build-deb ]; then
        if [ ! -f build-deb/${GEM_DEB_PACKAGE}_*.deb ]; then
            echo "'build-deb' directory already exists but .deb file package was not found"
            return 1

        fi
    else
        $0 $BUILD_FLAGS
    fi

    #
    #  prepare repo and install $GEM_DEB_PACKAGE package
    cd build-deb
    dpkg-scanpackages . /dev/null >Packages
    cat Packages | gzip -9c > Packages.gz
    dpkg-scansources . > Sources
    cat Sources | gzip > Sources.gz
    cat > Release <<EOF
Archive: precise
Origin: Ubuntu
Label: Local Ubuntu Precise Repository
Architecture: amd64
MD5Sum:
EOF
    printf ' '$(md5sum Packages | cut --delimiter=' ' --fields=1)' %16d Packages\n' \
        $(wc --bytes Packages | cut --delimiter=' ' --fields=1) >> Release
    printf ' '$(md5sum Packages.gz | cut --delimiter=' ' --fields=1)' %16d Packages.gz\n' \
        $(wc --bytes Packages.gz | cut --delimiter=' ' --fields=1) >> Release
    printf ' '$(md5sum Sources | cut --delimiter=' ' --fields=1)' %16d Sources\n' \
        $(wc --bytes Sources | cut --delimiter=' ' --fields=1) >> Release
    printf ' '$(md5sum Sources.gz | cut --delimiter=' ' --fields=1)' %16d Sources.gz\n' \
        $(wc --bytes Sources.gz | cut --delimiter=' ' --fields=1) >> Release
    gpg --armor --detach-sign --output Release.gpg Release
    cd -

    #
    #  check if an istance with the same address already exists
    export haddr="10.0.3.$le_addr"
    running_machines="$(sudo lxc-list | sed -n '/RUNNING/,/FROZEN/p' | egrep -v '^RUNNING$|^FROZEN$|^ *$' | sed 's/^ *//g')"
    for running_machine in $running_machines ; do
        if sudo grep -q "[^#]*address[ 	]\+$haddr[ 	]*$" /var/lib/lxc/${running_machine}/rootfs/etc/network/interfaces >/dev/null 2>&1; then
            echo -n "The $haddr machine seems to be already configured ... "
            set +e
            sudo lxc-shutdown -n $running_machine -w -t 10
            set -e
            echo "turned off"
        fi
    done

    #
    #  run the VM and get the VM name
    sudo lxc-start-ephemeral-gem -i $le_addr -d -o ubuntu-lxc >${haddr}.lxc.log 2>&1

    # waiting VM startup
    for i in $(seq 1 60); do
        if grep -q "is running" ${haddr}.lxc.log 2>/dev/null; then
            machine_name="$(grep "is running" ${haddr}.lxc.log | sed 's/ is running.*//g')"
            echo "MACHINE NAME: [$machine_name]"
            for e in $(seq 1 60); do
                sleep 1
                if lxc-ps -n "${machine_name}" | grep sshd; then
                    sleep 1
                    break
                fi
            done
            break
        fi
        sleep 1
    done
    if [ $i -eq 60 -o $e -eq 60 ]; then
        echo "VM not responding"
        return 2
    fi
    set +e
    _pkgtest_innervm_run $haddr
    inner_ret=$?
    sudo lxc-shutdown -n $machine_name -w -t 10
    set -e

    if [ $inner_ret -ne 0 ]; then
        return $inner_ret
    fi

    if [ $BUILD_REPOSITORY -eq 1 -a -d "${GEM_DEB_REPO}" ]; then
        mkdir -p "${GEM_DEB_REPO}/${GEM_DEB_SERIE}"
        repo_tmpdir="$(mktemp -d "${GEM_DEB_REPO}/${GEM_DEB_SERIE}/${GEM_DEB_PACKAGE}.XXXXXX")"
        cp build-deb/${GEM_DEB_PACKAGE}_*.deb build-deb/${GEM_DEB_PACKAGE}_*.changes \
            build-deb/${GEM_DEB_PACKAGE}_*.dsc build-deb/${GEM_DEB_PACKAGE}_*.tar.gz \
            build-deb/Packages* build-deb/Sources* build-deb/Release* "${repo_tmpdir}"
        if [ "${GEM_DEB_REPO}/${GEM_DEB_SERIE}/${GEM_DEB_PACKAGE}" ]; then
            rm -rf "${GEM_DEB_REPO}/${GEM_DEB_SERIE}/${GEM_DEB_PACKAGE}"
        fi
        mv "${repo_tmpdir}" "${GEM_DEB_REPO}/${GEM_DEB_SERIE}/${GEM_DEB_PACKAGE}"
    fi

    # TODO
    # app related tests (run demos)

    return
}

#
#  MAIN
#
BUILD_BINARIES=0
BUILD_REPOSITORY=0
BUILD_DEVEL=0
BUILD_UNSIGN=0
BUILD_FLAGS=""
#  args management
while [ $# -gt 0 ]; do
    case $1 in
        -D|--development)
            BUILD_DEVEL=1
            if [ "$DEBFULLNAME" = "" -o "$DEBEMAIL" = "" ]; then
                echo
                echo "error: set DEBFULLNAME and DEBEMAIL environment vars and run again the script"
                echo
                exit 1
            fi
            ;;
        -B|--binaries)
            BUILD_BINARIES=1
            ;;
        -R|--repository)
            BUILD_REPOSITORY=1
            ;;
        -U|--unsigned)
            BUILD_UNSIGN=1
            ;;
        -h|--help)
            usage 0
            break
            ;;
        pkgtest)
            pkgtest_run $2
            exit $?
            break
            ;;
        *)
            usage 1
            break
            ;;
    esac
    BUILD_FLAGS="$BUILD_FLAGS $1"    
    shift
done

DPBP_FLAG=""
if [ $BUILD_BINARIES -eq 0 ]; then
    DPBP_FLAG="-S"
fi
if [ $BUILD_UNSIGN -eq 1 ]; then
    DPBP_FLAG="$DPBP_FLAG -us -uc"
fi

mksafedir "$GEM_BUILD_ROOT"
mksafedir "$GEM_BUILD_SRC"

git archive HEAD | (cd "$GEM_BUILD_SRC" ; tar xv)

# NOTE: if in the future we need modules we need to execute the following commands
# 
# git submodule init
# git submodule update
##  "submodule foreach" vars: $name, $path, $sha1 and $toplevel:
# git submodule foreach "git archive HEAD | (cd \"\${toplevel}/${GEM_BUILD_SRC}/\$path\" ; tar xv ) "

cd "$GEM_BUILD_SRC"

# date
dt="$(date +%s)"

# version from setup.py
stp_vers="$(cat setup.py | grep "^version[ 	]*=[ 	]*['\"]" | sed -n "s/^version[ 	]*=[ 	]*['\"]//g;s/['\"].*//gp")"
stp_maj="$(echo "$stp_vers" | sed -n 's/^\([0-9]\+\).*/\1/gp')"
stp_min="$(echo "$stp_vers" | sed -n 's/^[0-9]\+\.\([0-9]\+\).*/\1/gp')"
stp_bfx="$(echo "$stp_vers" | sed -n 's/^[0-9]\+\.[0-9]\+\.\([0-9]\+\).*/\1/gp')"
stp_suf="$(echo "$stp_vers" | sed -n 's/^[0-9]\+\.[0-9]\+\.[0-9]\+\(.*\)/\1/gp')"
# echo "stp [$stp_vers] [$stp_maj] [$stp_min] [$stp_bfx] [$stp_suf]"

if [ 1 -eq 1 ]; then
    # version info from openquake/__init__.py
    ini_maj="$(cat openquake/engine/__init__.py | grep '# major' | sed -n 's/^[ ]*//g;s/,.*//gp')"
    ini_min="$(cat openquake/engine/__init__.py | grep '# minor' | sed -n 's/^[ ]*//g;s/,.*//gp')"
    ini_bfx="$(cat openquake/engine/__init__.py | grep '# sprint number' | sed -n 's/^[ ]*//g;s/,.*//gp')"
    ini_suf="" # currently not included into the version array structure
    # echo "ini [] [$ini_maj] [$ini_min] [$ini_bfx] [$ini_suf]"
else
    ini_maj="$stp_maj"
    ini_min="$stp_min"
    ini_bfx="$stp_bfx"
    ini_suf="$stp_suf"
fi

# version info from debian/changelog
h="$(head -n1 debian/changelog)"
# pkg_vers="$(echo "$h" | cut -d ' ' -f 2 | cut -d '(' -f 2 | cut -d ')' -f 1 | sed -n 's/[-+].*//gp')"
pkg_name="$(echo "$h" | cut -d ' ' -f 1)"
pkg_vers="$(echo "$h" | cut -d ' ' -f 2 | cut -d '(' -f 2 | cut -d ')' -f 1)"
pkg_rest="$(echo "$h" | cut -d ' ' -f 3-)"
pkg_maj="$(echo "$pkg_vers" | sed -n 's/^\([0-9]\+\).*/\1/gp')"
pkg_min="$(echo "$pkg_vers" | sed -n 's/^[0-9]\+\.\([0-9]\+\).*/\1/gp')"
pkg_bfx="$(echo "$pkg_vers" | sed -n 's/^[0-9]\+\.[0-9]\+\.\([0-9]\+\).*/\1/gp')"
pkg_deb="$(echo "$pkg_vers" | sed -n 's/^[0-9]\+\.[0-9]\+\.[0-9]\+\(-[^+]\+\).*/\1/gp')"
pkg_suf="$(echo "$pkg_vers" | sed -n 's/^[0-9]\+\.[0-9]\+\.[0-9]\+-[^+]\+\(+.*\)/\1/gp')"
# echo "pkg [$pkg_vers] [$pkg_maj] [$pkg_min] [$pkg_bfx] [$pkg_deb] [$pkg_suf]"

if [ $BUILD_DEVEL -eq 1 ]; then
    hash="$(git log --pretty='format:%h' -1)"
    mv debian/changelog debian/changelog.orig

    if [ "$pkg_maj" = "$ini_maj" -a "$pkg_min" = "$ini_min" -a \
         "$pkg_bfx" = "$ini_bfx" -a "$pkg_deb" != "" ]; then
        deb_ct="$(echo "$pkg_deb" | sed 's/^-//g')"
        pkg_deb="-$(( deb_ct + 1 ))"
    else
        pkg_maj="$ini_maj"
        pkg_min="$ini_min"
        pkg_bfx="$ini_bfx"
        pkg_deb="-1"
    fi

    ( echo "$pkg_name (${pkg_maj}.${pkg_min}.${pkg_bfx}${pkg_deb}+dev${dt}-${hash}) $pkg_rest"
      echo
      echo "  * Development version from $hash commit"
      echo
      echo " -- $DEBFULLNAME <$DEBEMAIL>  $(date -d@$dt -R)"
      echo
    )  > debian/changelog
    cat debian/changelog.orig >> debian/changelog
    rm debian/changelog.orig
fi

if [  "$ini_maj" != "$pkg_maj" -o "$ini_maj" != "$stp_maj" -o \
      "$ini_min" != "$pkg_min" -o "$ini_min" != "$stp_min" -o \
      "$ini_bfx" != "$pkg_bfx" -o "$ini_bfx" != "$stp_bfx" ]; then
    echo
    echo "Versions are not aligned"
    echo "    init:  ${ini_maj}.${ini_min}.${ini_bfx}"
    echo "    setup: ${stp_maj}.${stp_min}.${stp_bfx}"
    echo "    pkg:   ${pkg_maj}.${pkg_min}.${pkg_bfx}"
    echo
    echo "press [enter] to continue, [ctrl+c] to abort"
    read a
fi

if [ 1 -eq 1 ]; then
    sed -i "s/^\([ 	]*\)[^)]*\()  # release date .*\)/\1${dt}\2/g" openquake/__init__.py

    # mods pre-packaging
    mv LICENSE         openquake/engine
    mv README.txt      openquake/engine/README
    mv celeryconfig.py openquake/engine
    mv openquake.cfg   openquake/engine

    mv bin/openquake   bin/oqscript.py
    mv bin             openquake/engine/bin

    rm -rf $(find demos -mindepth 1 -maxdepth 1 | egrep -v 'demos/simple_fault_demo_hazard|demos/event_based_hazard|demos/_site_model')
fi

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
cp  ${GEM_BUILD_ROOT}/${GEM_DEB_PACKAGE}_*.deb  $GEM_BUILD_PKG
cd "$GEM_BUILD_EXTR"
dpkg -x $GEM_BUILD_PKG/${GEM_DEB_PACKAGE}_*.deb .
dpkg -e $GEM_BUILD_PKG/${GEM_DEB_PACKAGE}_*.deb
