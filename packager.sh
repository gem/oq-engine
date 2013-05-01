#!/bin/bash
# export PS4='+${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]}: '
set -x
set -e
GEM_GIT_REPO="git://github.com/gem"
GEM_GIT_PACKAGE="oq-engine"
GEM_GIT_DEPS="oq-nrmllib oq-hazardlib oq-risklib"
GEM_DEB_PACKAGE="python-${GEM_GIT_PACKAGE}"
GEM_DEB_SERIE="master"
if [ -z "$GEM_DEB_REPO" ]; then
    GEM_DEB_REPO="$HOME/gem_ubuntu_repo"
fi
GEM_BUILD_ROOT="build-deb"
GEM_BUILD_SRC="${GEM_BUILD_ROOT}/${GEM_DEB_PACKAGE}"

GEM_ALWAYS_YES=false

GEM_EPHEM_NAME="ubuntu-lxc-eph"

NL="
"
TB="	"

#
#  functions
sig_hand () {
    trap ERR
    echo "signal trapped"
    if [ "$lxc_name" != "" ]; then
        set +e
        echo "Destroying [$lxc_name] lxc"
        upper="$(mount | grep "${lxc_name}.*upperdir" | sed 's@.*upperdir=@@g;s@,.*@@g')"
        sudo lxc-stop -n $lxc_name
        sudo umount /var/lib/lxc/$lxc_name/rootfs
        sudo umount /var/lib/lxc/$lxc_name/ephemeralbind
        echo "$upper" | grep -q '^/tmp/'
        if [ $? -eq 0 ]; then
            sudo umount "$upper"
            sudo rm -r "$upper"
        fi
        sudo lxc-destroy -n $lxc_name
    fi
}

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
    echo "    $0 pkgtest <branch-name>                    run packaging tests into an ubuntu lxc environment"
    echo "    $0 devtest <branch-name>                    run development tests into an ubuntu lxc environment"
    echo
    exit $ret
}

_wait_ssh () {
    local lxc_ip="$1"

    for i in $(seq 1 20); do
        if ssh $lxc_ip "echo begin"; then
            break
        fi
        sleep 2
    done
    if [ $i -eq 20 ]; then
        return 1
    fi
}

_devtest_innervm_run () {
    local i old_ifs pkgs_list dep branch_id="$1" lxc_ip="$2"

    trap 'local LASTERR="$?" ; trap ERR ; (exit $LASTERR) ; return' ERR

    ssh $lxc_ip "sudo apt-get update"
    ssh $lxc_ip "sudo apt-get upgrade -y"

    old_ifs="$IFS"
    IFS=" "
    for dep in $GEM_GIT_DEPS; do
        # extract dependencies for source dependencies
        pkgs_list="$(deps_list "deprec" _jenkins_deps/$dep/debian/control)"
        ssh $lxc_ip "sudo apt-get install -y ${pkgs_list}"

        # install source dependencies
        cd _jenkins_deps/$dep
        git archive --prefix ${dep}/ HEAD | ssh $lxc_ip "tar xv"
        cd -
    done
    IFS="$old_ifs"

    # extract dependencies for this package
    pkgs_list="$(deps_list "all" debian/control)"
    ssh $lxc_ip "sudo apt-get install -y ${pkgs_list}"

    # install sources of this package
    git archive --prefix ${GEM_GIT_PACKAGE}/ HEAD | ssh $lxc_ip "tar xv"

    # configure the machine to run tests
    ssh $lxc_ip "echo \"local   all             \$USER          trust\" | sudo tee -a /etc/postgresql/9.1/main/pg_hba.conf"
    ssh $lxc_ip "sudo sed -i 's/#standard_conforming_strings = on/standard_conforming_strings = off/g' /etc/postgresql/9.1/main/postgresql.conf"

    ssh $lxc_ip "sudo service postgresql restart"
    ssh $lxc_ip "sudo -u postgres  createuser -d -e -i -l -s -w \$USER"
    ssh $lxc_ip "sudo -u postgres cd oq-engine ; bin/create_oq_schema --yes --db-user=\$USER --db-name=openquake --no-tab-spaces --schema-path=\$(pwd)/openquake/engine/db/schema"
    # run celeryd daemon
    ssh $lxc_ip "cd oq-engine ; celeryd >/tmp/celeryd.log 2>&1 3>&1 &"









    # TODO: version check
    echo "NOW PRESS ENTER TO CONTINUE"
    read aaa
    # ssh $lxc_ip "cd $GEM_GIT_PACKAGE ; PYTHONPATH="." ./run_tests"
    trap ERR

    return
}

_pkgtest_innervm_run () {
    local lxc_ip="$1"

    trap 'local LASTERR="$?" ; trap ERR ; (exit $LASTERR) ; return' ERR

    ssh $lxc_ip "sudo apt-get update"
    ssh $lxc_ip "sudo apt-get -y upgrade"
    gpg -a --export | ssh $lxc_ip "sudo apt-key add -"
    # install package to manage repository properly
    ssh $lxc_ip "sudo apt-get install -y python-software-properties"

    # create a remote "local repo" where place $GEM_DEB_PACKAGE package
    ssh $lxc_ip mkdir -p repo/${GEM_DEB_PACKAGE}
    scp build-deb/${GEM_DEB_PACKAGE}_*.deb build-deb/${GEM_DEB_PACKAGE}_*.changes \
        build-deb/${GEM_DEB_PACKAGE}_*.dsc build-deb/${GEM_DEB_PACKAGE}_*.tar.gz \
        build-deb/Packages* build-deb/Sources*  build-deb/Release* $lxc_ip:repo/${GEM_DEB_PACKAGE}
    ssh $lxc_ip "sudo apt-add-repository \"deb file:/home/ubuntu/repo/${GEM_DEB_PACKAGE} ./\""
# TODO: use the correct repo

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







    ssh $lxc_ip "sudo apt-get update"

    # packaging related tests (install, remove, purge, install, reinstall)
    ssh $lxc_ip "sudo apt-get install -y ${GEM_DEB_PACKAGE}"
    ssh $lxc_ip "sudo apt-get remove -y ${GEM_DEB_PACKAGE}"
    ssh $lxc_ip "sudo apt-get install -y ${GEM_DEB_PACKAGE}"
    ssh $lxc_ip "sudo apt-get install --reinstall -y ${GEM_DEB_PACKAGE}"

    # configure the machine to run tests
    ssh $haddr "echo \"local   all             \$USER          trust\" | sudo tee -a /etc/postgresql/9.1/main/pg_hba.conf"
    ssh $haddr "sudo sed -i 's/#standard_conforming_strings = on/standard_conforming_strings = off/g' /etc/postgresql/9.1/main/postgresql.conf"

    ssh $haddr "sudo service postgresql restart"
    ssh $haddr "sudo -u postgres  createuser -d -e -i -l -s -w \$USER"
    ssh $haddr "oq_create_db --yes --db-user=\$USER --db-name=openquake --no-tab-spaces --schema-path=/usr/share/pyshared/openquake/engine/db/schema"

    # run celeryd daemon
    ssh $haddr "cd /usr/openquake/engine ; celeryd >/tmp/celeryd.log 2>&1 3>&1 &"

    # copy demos file to $HOME
    ssh $haddr "cp -a /usr/share/doc/${GEM_DEB_PACKAGE}/examples/demos ."

    # run all demos found
    ssh $haddr "cd demos
    for ini in \$(find . -name job.ini); do
        DJANGO_SETTINGS_MODULE=openquake.engine.settings openquake --run-hazard  \$ini --exports xml
    done"

    trap ERR

    return
}

deps_list() {
    local oldifs out_list skip i d listtype="$1" filename="$2"

    oldifs="$IFS"
    IFS=','
    out_list=""
    if [ "$listtype" = "all" ]; then
        in_list="$(cat "$filename" | egrep '^Depends:|^Recommends:|Build-Depends:' | sed 's/^\(Build-\)\?Depends://g;s/^Recommends://g' | tr '\n' ',')"
    elif [  "$listtype" = "deprec" ]; then
        in_list="$(cat "$filename" | egrep '^Depends:|^Recommends:' | sed 's/^Depends://g;s/^Recommends://g' | tr '\n' ',')"
    elif [  "$listtype" = "build" ]; then
        in_list="$(cat "$filename" | egrep '^Depends:|^Build-Depends:' | sed 's/^\(Build-\)\?Depends://g' | tr '\n' ',')"
    else
        in_list="$(cat "$filename" | egrep "^Depends:" | sed 's/^Depends: //g')"
    fi

    for i in $in_list ; do
        item="$(echo "$i" |  sed 's/^ \+//g;s/ \+$//g')"
        pkg_name="$(echo "${item} " | cut -d ' ' -f 1)"
        pkg_vers="$(echo "${item} " | cut -d ' ' -f 2)"
        echo "[$pkg_name][$pkg_vers]" >&2
        if echo "$pkg_name" | grep -q "^\${" ; then
            continue
        fi
        skip=0
        for d in $(echo "$GEM_GIT_DEPS" | sed 's/ /,/g'); do
            if [ "$pkg_name" = "python-${d}" ]; then
                skip=1
                break
            fi
        done
        if [ $skip -eq 1 ]; then
            continue
        fi

        if [ "$out_list" = "" ]; then
            out_list="$pkg_name"
        else
            out_list="$out_list $pkg_name"
        fi
    done
    IFS="$oldifs"

    echo "$out_list"

    return 0
}

_lxc_name_and_ip_get()
{
    local filename="$1" i e

    i=-1
    e=-1
    for i in $(seq 1 40); do
        sleep 2
        if grep -q "sudo lxc-console -n $GEM_EPHEM_NAME" /tmp/packager.eph.$$.log 2>&1 ; then
            lxc_name="$(grep "sudo lxc-console -n $GEM_EPHEM_NAME" /tmp/packager.eph.$$.log | sed "s/.*sudo lxc-console -n \($GEM_EPHEM_NAME\)/\1/g")"
            for e in $(seq 1 40); do
                sleep 2
                if grep -q "$lxc_name" /var/lib/misc/dnsmasq.leases ; then
                    lxc_ip="$(grep " $lxc_name " /var/lib/misc/dnsmasq.leases | cut -d ' ' -f 3)"
                    break
                fi
            done
            break
        fi
    done
    if [ $i -eq 40 -o $e -eq 40 ]; then
        return 1
    fi
    echo "SUCCESSFULY RUNNED $lxc_name ($lxc_ip)"

    return 0
}

devtest_run () {
    local deps old_ifs branch_id="$1"

    mkdir _jenkins_deps

    sudo echo
    sudo lxc-start-ephemeral -o $GEM_EPHEM_NAME -d 2>&1 | tee /tmp/packager.eph.$$.log &
    _lxc_name_and_ip_get /tmp/packager.eph.$$.log

    _wait_ssh $lxc_ip

    repo_id="$(git remote -vv | grep '(fetch)$' | sed "s/^[^ ${TB}]\+[ ${TB}]\+git:\/\///g;s/.git[ ${TB}]\+(fetch)$/.git/g;s@/${GEM_GIT_PACKAGE}.git@@g")"
    if [ "$repo_id" != "$GEM_GIT_REPO" ]; then
        repos="${repo_id} ${GEM_GIT_REPO}"
    else
        repos="${GEM_GIT_REPO}"
    fi
    old_ifs="$IFS"
    IFS=" "
    for dep in $GEM_GIT_DEPS; do
        found=0
        branch="$branch_id"
        for repo in $repos; do
            # search of same branch in same repo or in GEM_GIT_REPO repo
            if git ls-remote --heads $repo/${dep}.git | grep -q "refs/heads/$branch" ; then
                git clone -b $branch $repo/${dep}.git _jenkins_deps/$dep
                found=1
                break
            fi
        done
        # if not found it fallback in master branch of GEM_GIT_REPO repo
        if [ $found -eq 0 ]; then
            git clone $repo/${dep}.git _jenkins_deps/$dep
            branch="master"
        fi
        var_pref="$(echo "$dep" | sed 's/[-.]/_/g;s/\(.*\)/\U\1/g')"
        echo "${var_pref}_REPO=$repo" >> _jenkins_deps_info
        echo "${var_pref}_BRANCH=$branch" >> _jenkins_deps_info
    done
    IFS="$old_ifs"

    set +e
    _devtest_innervm_run "$branch_id" "$lxc_ip"
    inner_ret=$?
    sudo lxc-shutdown -n $lxc_name -w -t 10
    set -e

    if [ -f /tmp/packager.eph.$$.log ]; then
        rm /tmp/packager.eph.$$.log
    fi

    # if [ $inner_ret -ne 0 ]; then
    return $inner_ret
    # fi
}

pkgtest_run () {
    local i e branch_id="$1"

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

    sudo echo
    sudo lxc-start-ephemeral -o $GEM_EPHEM_NAME -d 2>&1 | tee /tmp/packager.eph.$$.log &
    _lxc_name_and_ip_get /tmp/packager.eph.$$.log

    _wait_ssh $lxc_ip

    set +e
    _pkgtest_innervm_run $lxc_ip
    inner_ret=$?
    sudo lxc-shutdown -n $lxc_name -w -t 10
    set -e

    if [ -f /tmp/packager.eph.$$.log ]; then
        rm /tmp/packager.eph.$$.log
    fi

    if [ $inner_ret -ne 0 ]; then
        return $inner_ret
    fi

    if [ $BUILD_REPOSITORY -eq 1 -a -d "${GEM_DEB_REPO}" ]; then
        if [ "${branch_id}" != "" ]; then
            CUSTOM_SERIE="devel/$(git remote -vv | grep '(fetch)$' | sed "s/^[^ ${TB}]\+[ ${TB}]\+git:\/\///g;s/.git[ ${TB}]\+(fetch)$//g;s@/$GEM_GIT_PACKAGE@@g;s@/@__@g;s/\./-/g")__${branch_id}"
            if [ "$CUSTOM_SERIE" != "" ]; then
                GEM_DEB_SERIE="$CUSTOM_SERIE"
            fi
        fi
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

    return 0
}

#
#  MAIN
#
BUILD_BINARIES=0
BUILD_REPOSITORY=0
BUILD_DEVEL=0
BUILD_UNSIGN=0
BUILD_FLAGS=""

trap sig_hand SIGINT SIGTERM
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
        devtest)
            devtest_run $2
            exit $?
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
stp_vers="$(cat setup.py | grep "^version[     ]*=[    ]*['\"]" | sed -n "s/^version[  ]*=[    ]*['\"]//g;s/['\"].*//gp")"
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
    sed -i "s/^\([ ${TB}]*\)[^)]*\()  # release date .*\)/\1${dt}\2/g" openquake/__init__.py

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
