#!/bin/bash
set -e
# set -x

debconf_override=0

sig_hand () {
    # if overrided recover origina .debconfrc file
    if [ "$debconf_override" -eq 1 ]; then
        mv "$HOME/debconfrc.msc.orig" "$HOME/.debconfrc"
    fi
}

prepare_rootfs () {
    local pkgname="$1" scenario="$2" to_del

    mkdir "${BDIR}/curr/rootfs"
    cp -a "${BDIR}/orig/rootfs/"* "${BDIR}/curr/rootfs"
    cp -a "${BDIR}/test/$pkgname/$scenario/rootfs/"* "${BDIR}/curr/rootfs"
    for to_del in $(find "${BDIR}/curr" -name '*.delete'); do
        realname="$(echo "$to_del" | sed 's/\.delete$//g')"
        if [ -d "$realname" ]; then
            rm -rf "$realname"
            rm "$to_del"
            echo "[$realname] directory deleted"
        elif [ -f "$realname" ]; then
            rm "$realname"
            rm "$to_del"
            echo "[$realname] file deleted"
        else
            echo "$realname not found and not deleted"
            return 1
        fi
    done
}

prepare_debconf () {
    local pkgname="$1" scenario="$2" debconf="$3" to_del
    
    mkdir "${BDIR}/curr/debconf"
    
    cp -a "${BDIR}/orig/debconf/$pkgname/"* "${BDIR}/curr/debconf"
    cp -a "${BDIR}/test/$pkgname/$scenario/$debconf/"* "${BDIR}/curr/debconf"
    for to_del in $(find "${BDIR}/curr" -name '*.delete'); do
        realname="$(echo "$to_del" | sed 's/\.delete$//g')"
        if [ -d "$realname" ]; then
            rm -rf "$realname"
            rm "$to_del"
            echo "[$realname] directory deleted"
        elif [ -f "$realname" ]; then
            rm "$realname"
            rm "$to_del"
            echo "[$realname] file deleted"
        else
            echo "$realname not found and not deleted"
            return 1
        fi
    done
}

curr_snapshot () {
    local debconf="$1" dname="$2"

    cp -a "${BDIR}/curr/rootfs" "${BDIR}/curr/rootfs.${debconf}.${dname}"
    cp -a "${BDIR}/curr/debconf" "${BDIR}/curr/debconf.${debconf}.${dname}"
}

custom_debconfrc () {
    local dcpath="$1"
    
    # if exists save the original .debconfrc
    if [ -f "$HOME/.debconfrc" ]; then
        mv "$HOME/.debconfrc" "$HOME/debconfrc.msc.orig"
        debconf_override=1
    fi
    
    # create the new .debconfrc
    cat <<EOF | sed "s@#DEBCONFPATH#@$dcpath@g" >"$HOME/.debconfrc"
Config: configdb
Templates: templatedb

Name: config
Driver: File
Mode: 644
Reject-Type: password
Filename: #DEBCONFPATH#/config.dat

Name: passwords
Driver: File
Mode: 600
Backup: false
Required: false
Accept-Type: password
Filename: #DEBCONFPATH#/passwords.dat

Name: configdb
Driver: Stack
Stack: config, passwords

Name: templatedb
Driver: File
Mode: 644
Filename: #DEBCONFPATH#/templates.dat

EOF
    
}

perform_test () {
    local pkgname="$1" scenario="$2" debconf="$3"

    echo
    echo "Package: $pkgname  Scenario: $scenario  Debconf: $debconf"
#return 0    
    if [ -d "${BDIR}/curr" ]; then
        rm -rf "${BDIR}/curr"
    fi
    mkdir "${BDIR}/curr"
    
    prepare_rootfs "$pkgname" "$scenario"
    prepare_debconf "$pkgname" "$scenario" "$debconf"
    
    # save the original state
    curr_snapshot "$debconf" step0
    
    # run first configure
    debian/${pkgname}.postinst configure

    curr_snapshot "$debconf" step1

    checkpoint "$pkgname" "$scenario" "$debconf" 1 

checkpoint () {
    local pkgname="$1" scenario="$2" debconf="$3" step="$4"
    cd "${BDIR}"
    df="$(diff -r curr/rootfs.${debconf}.step${step} curr/rootfs || true)"
    cd -
    if ! echo "$df" | diff -q ${BDIR}/test/${pkgname}/${scenario}/step0_${debconf}.diff - >/dev/null 2>&1 ; then        
        echo "DIFFER"
        echo "$df" > "${BDIR}/curr/${pkgname}__${scenario}__${debconf}__step$((step - 1))_step${step}.diff"
        return 1
    fi
}

    curr_snapshot "$debconf" step1

#    debian/${pkgname}.postrm

#    curr_snapshot "$debconf" step2

#    debian/${pkgname}.postinst configure

#    curr_snapshot "$debconf" step3

    debian/${pkgname}.postrm purge

    curr_snapshot "$debconf" step4


    return 0
}



#
#  MAIN
#

trap sig_hand SIGINT SIGTERM ERR
export BDIR="$(echo "$(pwd)/$(dirname $0)/.." | sed 's@/\./@/@g')"

if [ $# -eq 3 ]; then
    pkgname_target="$1"
    scenario_target="$2"
    debconf_target="$3"
else
    pkgname_target=".*"
    scenario_target=".*"
    debconf_target=".*"
fi

# set the fakeroot for all tests
export GEM_FAKEROOT="${BDIR}/curr/rootfs"

custom_debconfrc "${BDIR}/curr/debconf"

for pkgname in $(echo "python-oq-engine-master" | grep "$pkgname_target") ; do
    export DPKG_MAINTSCRIPT_PACKAGE="$pkgname"
    export DEBCONF_DEBUG=developer 
    export DEBCONF_PACKAGE="$pkgname"
    for scenario in $(ls ${BDIR}/test/$pkgname | grep "$scenario_target"); do
        for debconf in $(ls ${BDIR}/test/$pkgname/$scenario | grep '^debconf.*$' | grep "$debconf_target"); do
            perform_test "$pkgname" "$scenario" "$debconf"
        done
    done
done


exit 0