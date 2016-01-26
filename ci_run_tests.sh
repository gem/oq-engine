#!/bin/bash
#
#  ci_run_tests.sh  Copyright (c) 2015, GEM Foundation.
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

#
# DESCRIPTION
#
# tests are performed inside linux containers (lxc) to achieve
# a good compromise between speed and isolation
#
# all lxc instances are ephemeral
#
# ephemeral containers are "clones" of a base container and have a
# temporary file system that reflects the contents of the base container
# but any modifications are stored in another overlayed
# file system (in-memory or disk)
#

if [ -n "$GEM_SET_DEBUG" -a "$GEM_SET_DEBUG" != "false" ]; then
    export PS4='+${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]}: '
    set -x
fi
set -e
GEM_GIT_REPO="git://github.com/gem"
GEM_GIT_REPO2="git://github.com/GEMScienceTools"
GEM_GIT_PACKAGE="hmtk"
GEM_GIT_DEPS="oq-hazardlib oq-risklib oq-nrmllib oq-ipynb-runner notebooks"
GEM_PIP_DEPS="jupyter nose"

GEM_LOCAL_DEPS="python-virtualenv python-nose python-coverage gmt python-pyshp gmt-gshhs-low python-matplotlib python-mpltoolkits.basemap pylint python-lxml python-yaml"

if [ -z "$GEM_DEB_REPO" ]; then
    GEM_DEB_REPO="$HOME/gem_ubuntu_repo"
fi
if [ -z "$GEM_DEB_MONOTONE" ]; then
    GEM_DEB_MONOTONE="$HOME/monotone"
fi

GEM_BUILD_ROOT="build-deb"
GEM_BUILD_SRC="${GEM_BUILD_ROOT}/${GEM_DEB_PACKAGE}"

GEM_MAXLOOP=20

GEM_ALWAYS_YES=false

if [ "$GEM_EPHEM_CMD" = "" ]; then
    GEM_EPHEM_CMD="lxc-start-ephemeral"
fi
if [ "$GEM_EPHEM_NAME" = "" ]; then
    GEM_EPHEM_NAME="ubuntu14-x11-lxc-eph"
fi

if command -v lxc-shutdown &> /dev/null; then
    # Older lxc (< 1.0.0) with lxc-shutdown
    LXC_TERM="lxc-shutdown -t 10 -w"
    LXC_KILL="lxc-stop"
else
    # Newer lxc (>= 1.0.0) with lxc-stop only
    LXC_TERM="lxc-stop -t 10"
    LXC_KILL="lxc-stop -k"
fi

NL="
"
TB="	"

#
#  functions

#
#  sig_hand - manages cleanup if the build is aborted
#
sig_hand () {
    trap ERR
    echo "signal trapped"
    if [ "$lxc_name" != "" ]; then
        set +e
        scp "${lxc_ip}:ssh.log" "out_${BUILD_UBUVER}/ssh.history"
        # currently no tests are developed for gmpe-smtk, temporarily we use notebooks
        scp "${lxc_ip}:${GEM_GIT_PACKAGE}/nosetests*.xml" "out_${BUILD_UBUVER}/"
        echo "Destroying [$lxc_name] lxc"
        upper="$(mount | grep "${lxc_name}.*upperdir" | sed 's@.*upperdir=@@g;s@,.*@@g')"
        if [ -f "${upper}.dsk" ]; then
            loop_dev="$(sudo losetup -a | grep "(${upper}.dsk)$" | cut -d ':' -f1)"
        fi
        sudo $LXC_KILL -n $lxc_name
        sudo umount /var/lib/lxc/$lxc_name/rootfs
        sudo umount /var/lib/lxc/$lxc_name/ephemeralbind
        echo "$upper" | grep -q '^/tmp/'
        if [ $? -eq 0 ]; then
            sudo umount "$upper"
            sudo rm -r "$upper"
            if [ "$loop_dev" != "" ]; then
                sudo losetup -d "$loop_dev"
                if [ -f "${upper}.dsk" ]; then
                    sudo rm -f "${upper}.dsk"
                fi
            fi
        fi
        sudo lxc-destroy -n $lxc_name
    fi
    if [ -f /tmp/packager.eph.$$.log ]; then
        rm /tmp/packager.eph.$$.log
    fi
    exit 1
}


#
#  dep2var <dep> - converts in a proper way the name of a dependency to a variable name
#      <dep>    the name of the dependency
#
dep2var () {
    echo "$1" | sed 's/[-.]/_/g;s/\(.*\)/\U\1/g'
}

#
#  repo_id_get - retry git repo from local git remote command
repo_id_get () {
    local repo_name repo_line

    if ! repo_name="$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)"; then
        repo_line="$(git remote -vv | grep "^origin[ ${TB}]" | grep '(fetch)$')"
        if [ -z "$repo_line" ]; then
            echo "no remote repository associated with the current branch, exit 1"
            exit 1
        fi
    else
        repo_name="$(echo "$repo_name" | sed 's@/.*@@g')"

        repo_line="$(git remote -vv | grep "^${repo_name}[ ${TB}].*(fetch)\$")"
    fi

    if echo "$repo_line" | grep -q '[0-9a-z_-\.]\+@[a-z0-9_-\.]\+:'; then
        repo_id="$(echo "$repo_line" | sed "s/^[^ ${TB}]\+[ ${TB}]\+[^ ${TB}@]\+@//g;s/.git[ ${TB}]\+(fetch)$/.git/g;s@/${GEM_GIT_PACKAGE}.git@@g;s@:@/@g")"
    else
        repo_id="$(echo "$repo_line" | sed "s/^[^ ${TB}]\+[ ${TB}]\+git:\/\///g;s/.git[ ${TB}]\+(fetch)$/.git/g;s@/${GEM_GIT_PACKAGE}.git@@g")"
    fi

    echo "$repo_id"
}

#
#  mksafedir <dname> - try to create a directory and rise an alert if it already exists
#      <dname>    name of the directory to create
#
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

#
#  usage <exitcode> - show usage of the script
#      <exitcode>    value of exitcode
#
usage () {
    local ret

    ret=$1

    echo
    echo "USAGE:"
    echo "    $0 [<-s|--serie> <precise|trusty>]"
    echo "    $0 devtest <branch-name>"
    echo
    exit $ret
}

#
#  _wait_ssh <lxc_ip> - wait until the new lxc ssh daemon is ready
#      <lxc_ip>    the IP address of lxc instance
#
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


#
#  _devtest_innervm_run <lxc_ip> <branch> - part of source test performed on lxc
#                     the following activities are performed:
#                     - extracts dependencies from oq-{engine,hazardlib, ..} debian/control
#                       files and install them
#                     - builds oq-hazardlib speedups
#                     - installs oq-engine sources on lxc
#                     - set up postgres
#                     - upgrade db
#                     - runs celeryd
#                     - runs tests
#                     - runs coverage
#                     - collects all tests output files from lxc
#
#      <lxc_ip>   the IP address of lxc instance
#      <branch>   name of the tested branch
#
_devtest_innervm_run () {
    local i old_ifs pkgs_list dep lxc_ip="$1" branch="$2"

    trap 'local LASTERR="$?" ; trap ERR ; (exit $LASTERR) ; return' ERR

    ssh $lxc_ip "rm -f ssh.log"

    ssh $lxc_ip "sudo apt-get update"
    ssh $lxc_ip "sudo apt-get -y upgrade"
    gpg -a --export | ssh $lxc_ip "sudo apt-key add -"
    # install package to manage repository properly
    ssh $lxc_ip "sudo apt-get install -y python-software-properties"

    # add custom packages
    ssh $lxc_ip mkdir -p "repo"
if [ 0 -eq 1 ]; then
    scp -r ${GEM_DEB_REPO}/${BUILD_UBUVER}/custom_pkgs $lxc_ip:repo/custom_pkgs
    ssh $lxc_ip "sudo apt-add-repository \"deb file:/home/ubuntu/repo/custom_pkgs ./\""

    ssh $lxc_ip "sudo apt-get update"
    ssh $lxc_ip "sudo apt-get upgrade -y"
fi
    ssh $lxc_ip "sudo apt-get install -y $GEM_LOCAL_DEPS"

    old_ifs="$IFS"
    IFS=" "
    for dep in $GEM_GIT_DEPS; do
        # extract dependencies for source dependencies
        pkgs_list="$(deps_list "deprec" _jenkins_deps/$dep/debian)"
        if [ "$pkgs_list" ]; then
            ssh $lxc_ip "sudo apt-get install -y ${pkgs_list}"
        fi

        # install source dependencies
        cd _jenkins_deps/$dep
        git archive --prefix ${dep}/ HEAD | ssh $lxc_ip "tar xv"
        cd -
    done
    IFS="$old_ifs"

    # extract dependencies for this package
    pkgs_list="$(deps_list "all" debian)"
    if [ "$pkgs_list" ]; then
        ssh $lxc_ip "sudo apt-get install -y ${pkgs_list}"
    fi

    cat >.gem_init.sh <<EOF
export GEM_SET_DEBUG=$GEM_SET_DEBUG
set -e
if [ -n "\$GEM_SET_DEBUG" -a "\$GEM_SET_DEBUG" != "false" ]; then
    export PS4='+\${BASH_SOURCE}:\${LINENO}:\${FUNCNAME[0]}: '
    set -x
fi
EOF
    scp .gem_init.sh ${lxc_ip}:
    # build oq-hazardlib speedups and put in the right place
    ssh $lxc_ip "source .gem_init.sh
                 cd oq-hazardlib
                 python ./setup.py build
                 for i in \$(find build/ -name *.so); do
                     o=\"\$(echo \"\$i\" | sed 's@^[^/]\+/[^/]\+/@@g')\"
                     cp \$i \$o
                 done"

    # create virtualenv and install pip deps
    ssh $lxc_ip "source .gem_init.sh
                 virtualenv --system-site-packages ci-env
                 source ci-env/bin/activate
                 IFS=' '
                 for ppkg in $GEM_PIP_DEPS; do
                     pip install --upgrade \$ppkg
                 done"

    # install sources of this package
    git archive --prefix ${GEM_GIT_PACKAGE}/ HEAD | ssh $lxc_ip "tar xv"

    ssh $lxc_ip "source .gem_init.sh
                 source ci-env/bin/activate
                 ipython profile create
                 echo \"c = get_config()\"                      >> ~/.ipython/profile_default/ipython_config.py
                 echo \"c.InteractiveShell.colors = 'NoColor'\" >> ~/.ipython/profile_default/ipython_config.py

                 export PYTHONPATH=\"\$PWD/oq-hazardlib:\$PWD/oq-risklib:\$PWD/oq-nrmllib:\$PWD/oq-ipynb-runner\"
                 cd $GEM_GIT_PACKAGE
                 nosetests --with-xunit --xunit-file=nosetests.xml -v --with-coverage || true
                 cd -
                 cd notebooks/hmtk
                 # mkdir images
                 # unzip data/demo_records_full.zip -d data
                 export DISPLAY=\"$guest_display\"
                 nosetests --with-xunit --xunit-file=../../hmtk/nosetests_hmtk_notebooks.xml -v --with-coverage || true
                 deactivate"

    trap ERR

    return
}

#
#  deps_list <listtype> <filename> - retrieve dependencies list from debian/control
#                                    to be able to install them without the package
#      listtype    inform deps_list which control lines use to get dependencies
#      dir         the folder containing control and rules files
#
deps_list() {
    local old_ifs out_list skip i d listtype="$1" control_file="$2"/control rules_file="$2"/rules

    out_list=""

    if [ ! -f "${control_file}" ]; then
        echo "$out_list"
        return 0
    fi

    rules_dep=$(grep "^${BUILD_UBUVER^^}_DEP *= *" $rules_file | sed 's/^.*= *//g')
    rules_rec=$(grep "^${BUILD_UBUVER^^}_REC *= *" $rules_file | sed 's/^.*= *//g')

    if [ "$listtype" = "all" ]; then
        in_list="$((cat "$control_file" | egrep '^Depends:|^Recommends:|Build-Depends:' | sed 's/^\(Build-\)\?Depends://g;s/^Recommends://g' ; echo ", $rules_dep, $rules_rec") | tr '\n' ','| sed 's/,\+/,/g')"
    elif [  "$listtype" = "deprec" ]; then
        in_list="$((cat "$control_file" | egrep '^Depends:|^Recommends:' | sed 's/^Depends://g;s/^Recommends://g' ; echo ", $rules_dep, $rules_rec") | tr '\n' ','| sed 's/,\+/,/g')"
    elif [  "$listtype" = "build" ]; then
        in_list="$((cat "$control_file" | egrep '^Depends:|^Build-Depends:' | sed 's/^\(Build-\)\?Depends://g' ; echo ", $rules_dep") | tr '\n' ','| sed 's/,\+/,/g')"
    else
        in_list="$((cat "$control_file" | egrep "^Depends:" | sed 's/^Depends: //g'; echo ", $rules_dep") | tr '\n' ','| sed 's/,\+/,/g')"
    fi
    old_ifs="$IFS"
    IFS=','
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
    IFS="$old_ifs"
    echo "$out_list"
    return 0
}

#
#  _lxc_name_and_ip_get <filename> - retrieve name and ip of the runned ephemeral lxc and
#                                    put them into global vars "lxc_name" and "lxc_ip"
#      <filename>    file where lxc-start-ephemeral output is saved
#
_lxc_name_and_ip_get()
{
    local filename="$1" i e

    i=-1
    e=-1
    for i in $(seq 1 40); do
        sleep 2
        if grep -q "sudo lxc-console -n $GEM_EPHEM_NAME" $filename 2>&1 ; then
            lxc_name="$(grep "sudo lxc-console -n $GEM_EPHEM_NAME" $filename | grep -v '+ echo' | sed "s/.*sudo lxc-console -n \($GEM_EPHEM_NAME\)/\1/g")"
            for e in $(seq 1 40); do
                sleep 2
                if grep -q "$lxc_name" /var/lib/misc/dnsmasq*.leases ; then
                    lxc_ip="$(grep " $lxc_name " /var/lib/misc/dnsmasq*.leases | tail -n 1 | cut -d ' ' -f 3)"
                    break
                fi
            done
            break
        fi
    done
    if [ $i -eq 40 -o $e -eq 40 ]; then
        return 1
    fi
    echo "SUCCESSFULLY RUNNED $lxc_name ($lxc_ip)"

    return 0
}

# get guest DISPLAY value
_guest_display_get () {
    local lxc_ip="$1"

    ssh $lxc_ip 'x_list="$(ls /tmp/.X*-lock)"
for x in $(echo "$x_list"); do
    if sudo kill -0 $(cat $x) >/dev/null 2>&1; then
        echo "$x" | sed '"'"'s@^/tmp/.X@:@g;s@-lock$@@g'"'"'
        exit 0
    fi
done
exit 1'
}

deps_check_or_clone () {
    local dep="$1" repo="$2" branch="$3"
    local local_repo local_branch

    if [ -d _jenkins_deps/$dep ]; then
        cd _jenkins_deps/$dep
        local_repo="$(git remote -v | head -n 1 | sed 's/origin[ 	]\+//;s/ .*//g')"
        if [ "$local_repo" != "$repo" ]; then
            echo "Dependency $dep: cached repository version differs from required ('$local_repo' != '$repo')."
            exit 1
        fi
        local_branch="$(git branch 2>/dev/null | sed -e '/^[^*]/d' | sed -e 's/* \(.*\)/\1/')"
        if [ "$local_branch" != "$branch" ]; then
            echo "Dependency $dep: cached branch version differs from required ('$local_branch' != '$branch')."
            exit 1
        fi
        git clean -dfx
        cd -
    else
        git clone --depth=1 -b $branch $repo _jenkins_deps/$dep
    fi
}

#
#  devtest_run <branch> - main function of source test
#      <branch>    name of the tested branch
#
devtest_run () {
    local deps old_ifs branch="$1" branch_cur

    if [ ! -d "out_${BUILD_UBUVER}" ]; then
        mkdir "out_${BUILD_UBUVER}"
    fi

    if [ ! -d _jenkins_deps ]; then
        mkdir _jenkins_deps
    fi

    #
    #  dependencies repos
    #
    # in test sources different repositories and branches can be tested
    # consistently: for each openquake dependency it try to use
    # the same repository and the same branch OR the gem repository
    # and the same branch OR the gem repository and the "master" branch
    #
    repo_id="$(repo_id_get)"
    if [ "$repo_id" != "$GEM_GIT_REPO" -a "$repo_id" != "$GEM_GIT_REPO2" ]; then
        repos="git://${repo_id} ${GEM_GIT_REPO} ${GEM_GIT_REPO2}"
    else
        repos="${GEM_GIT_REPO} ${GEM_GIT_REPO2}"
    fi
    if [ "$branch" != "master" ]; then
        branches="$branch master"
    else
        branches="master"
    fi

    old_ifs="$IFS"
    IFS=" "
    for dep in $GEM_GIT_DEPS; do
        found=0
        for branch_cur in $branches; do
            for repo in $repos; do
                # search of same branch in same repo or in GEM_GIT_REPO repo
                if git ls-remote --heads $repo/${dep}.git | grep -q "refs/heads/$branch_cur" ; then
                    deps_check_or_clone "$dep" "$repo/${dep}.git" "$branch_cur"
                    found=1
                    break 2
                fi
            done
        done

        if [ $found -ne 1 ]; then
            echo "Dependency $dep not found."
            exit 1
        fi
        cd _jenkins_deps/$dep
        commit="$(git log -1 | grep '^commit' | sed 's/^commit //g')"
        cd -
        echo "dependency: $dep"
        echo "repo:       $repo"
        echo "branch:     $branch_cur"
        echo "commit:     $commit"
        echo
        var_pfx="$(dep2var "$dep")"
        if [ ! -f _jenkins_deps_info ]; then
            touch _jenkins_deps_info
        fi
        if grep -q "^${var_pfx}_COMMIT=" _jenkins_deps_info; then
            if ! grep -q "^${var_pfx}_COMMIT=$commit" _jenkins_deps_info; then
                echo "ERROR: $repo -> $branch_cur changed during test:"
                echo "before:"
                grep "^${var_pfx}_COMMIT=" _jenkins_deps_info
                echo "after:"
                echo "${var_pfx}_COMMIT=$commit"
                exit 1
            fi
        else
            echo "${var_pfx}_COMMIT=$commit" >> _jenkins_deps_info
            echo "${var_pfx}_REPO=$repo"     >> _jenkins_deps_info
            echo "${var_pfx}_BRANCH=$branch_cur" >> _jenkins_deps_info
        fi
    done
    IFS="$old_ifs"

    sudo echo
    sudo ${GEM_EPHEM_CMD} -o $GEM_EPHEM_NAME -d 2>&1 | tee /tmp/packager.eph.$$.log &
    _lxc_name_and_ip_get /tmp/packager.eph.$$.log

    _wait_ssh $lxc_ip
    guest_display="$(_guest_display_get "$lxc_ip")"

    set +e
    _devtest_innervm_run "$lxc_ip" "$branch"
    inner_ret=$?

    # currently no tests are developed for gmpe-smtk, temporarily we use notebooks
    scp "${lxc_ip}:${GEM_GIT_PACKAGE}/nosetests*.xml" "out_${BUILD_UBUVER}/" || true
    scp "${lxc_ip}:ssh.log" "out_${BUILD_UBUVER}/devtest.history" || true

    sudo $LXC_TERM -n $lxc_name

    # NOTE: pylint returns errors too frequently to consider them a critical event
    if pylint --rcfile pylintrc -f parseable oq_input oq_output > pylint.txt ; then
        echo "pylint exits without errors"
    else
        echo "WARNING: pylint exits with $? value"
    fi
    set -e
    if [ -f /tmp/packager.eph.$$.log ]; then
        rm /tmp/packager.eph.$$.log
    fi

    return $inner_ret
}

#
#  MAIN
#
BUILD_DEVEL=0
BUILD_UBUVER_REFERENCE="trusty"
BUILD_UBUVER="$BUILD_UBUVER_REFERENCE"

trap sig_hand SIGINT SIGTERM
#  args management
while [ $# -gt 0 ]; do
    case $1 in
        -s|--serie)
            BUILD_UBUVER="$2"
            if [ "$BUILD_UBUVER" != "precise" -a "$BUILD_UBUVER" != "trusty" ]; then
                echo
                echo "ERROR: ubuntu version '$BUILD_UBUVER' not supported"
                echo
                exit 1
            fi
            shift
            ;;
        -h|--help)
            usage 0
            break
            ;;
        devtest)
            # Sed removes 'origin/' from the branch name
            devtest_run $(echo "$2" | sed 's@.*/@@g')
            exit $?
            break
            ;;
        *)
            usage 1
            break
            ;;
    esac
    shift
done
