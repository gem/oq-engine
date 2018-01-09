#!/bin/bash
set -e
# set -x

line="------------------------------------------------------------"
doubleline="============================================================"

usage () {
    echo
    echo "USAGE:"
    echo "    $0 <branch_name>    check existence of branch for each required sibling repository"
    echo "        repos are searched or created in the same directory where oq-engine repo directory is placed"
    echo
    echo "    $0 <-h|--help>      this help"
    echo
    exit $1
}

#
#  MAIN
#
if [ $# -ne 1 -o "$1" = "-h" -o "$1" = "--help" ]; then
    usage 1
fi
branch="$1"

if [ ! -d ../oq-platform-standalone ]; then
    read -p "'../oq-platform-standalone' repository not exists, clone it ? " yn
    if [ "$yn" != "y" -a "$yn" != "Y" ]; then
        exit 1
    fi
    cd ..
    git clone git@github.com:gem/oq-platform-standalone.git
    cd -
fi

export PYTHONPATH="../oq-platform-standalone"
si_apps="$(python -c "from openquakeplatform.settings import STANDALONE_APPS ; print(' '.join(STANDALONE_APPS))")"
si_repos="oq-platform-standalone oq-libs oq-builders $(echo "$si_apps" | sed 's/openquakeplatform/oq-platform/g;s/_/-/g')"
pushd .. >/dev/null


for repo in $si_repos; do
    echo
    echo "===  $repo  $doubleline"
    echo
    verified="n"
    while [ "$verified" != "y" ]; do
        if [ ! -d "${repo}" ]; then
            read -p "'../${repo}' repository not exists, clone it ? " yn
            git clone "git@github.com:gem/${repo}.git"
            pushd "$repo" >/dev/null
        else
            pushd "$repo" >/dev/null
            git fetch origin >/dev/null 2>&1
        fi

        # check remote branch existence
        br_rem="n"
        git branch --list -r "origin/$branch" >/dev/null 2>&1
        if [ $(git branch --list -r "origin/$branch" 2>&1 | wc -l) -eq 1 ]; then
            hash_rem="$(git log -1 --pretty=format:"%h" "origin/$branch")"
            br_rem=y
        fi

        # check local branch existence
        br_loc="n"
        git branch --list "$branch" >/dev/null 2>&1
        if [ $(git branch --list "$branch" 2>&1 | wc -l) -eq 1 ]; then
            hash_loc="$(git log -1 --pretty=format:"%h" "$branch")"
            br_loc=y
        fi

        # if exists both local and remote branch
        if [ "$br_loc" = "y" -a "$br_rem" = "y" ]; then
            # verify hashes are equal
            if [ "$hash_loc" = "$hash_rem" ]; then
                echo "    remote and local branch found and are the same: $hash_loc"
            else
                echo "    local and remote branch found and ARE DIFFERENT: local: $hash_loc  remote: $hash_rem"
                read -p "to continue, in another console, fix it, than press 'Enter', otherwise press 'CTRL+C' to interrupt" yn
                popd >/dev/null
                echo "$line" ; echo
                continue
            fi

        # if exists just local branch
        elif [ "$br_loc" = "y" -a "$br_rem" = "n" ]; then
            echo "    local branch only found with hash $hash_loc"
            read -p "    to continue, in another console, push it to origin, than press 'Enter', otherwise press 'CTRL+C' to interrupt" yn
            popd >/dev/null
            echo "$line" ; echo
            continue

        # if exists just remote branch
        elif [ "$br_loc" = "n" -a "$br_rem" = "y" ]; then
            echo "    remote branch only found with hash $hash_rem"

        # if branch not exists at all give info about current branch and if you want to create and push it
        else
            echo "    neither local nor remote branch '$branch' exists"
            branch_cur="$(git branch | grep \* | cut -d ' ' -f2)"
            if [ "$branch_cur" == "" ]; then
                echo "    current local branch name not detected, abort"
                exit 1
            fi
            hash_cur="$(git log -1 --pretty=format:"%h")"
            if [ "$hash_cur" == "" ]; then
                echo "    current local hash not detected, abort"
                exit 1
            fi
            echo "    current branch is '$branch_cur', current hash is '$hash_cur'"

            # if exists a remote branch with the same name of the current check if local and
            # remote hashes are the same, raising a warning in the other case
            branch_rem_cur="$(git branch --list -r "origin/$branch_cur")"
            if [ "$branch_rem_cur" != "" ]; then
                hash_rem_cur="$(git log -1 --pretty=format:"%h" "origin/$branch_cur")"
                if [ "$hash_cur" != "$hash_rem_cur" ]; then
                    echo "    ==== WARNING ==== WARNING ==== WARNING ==== WARNING ==== WARNING ==== WARNING ===="
                    echo "    current branch '$branch_cur' exists remotely but hashes are different"
                    echo "    local hash: '$hash_cur',  remote hash: '$hash_rem_cur'"
                    read -p "    press 'Enter' to proceed, 'CTRL + C' to interrupt" yn
                fi
            fi

            read -p "    do you want to create and push it to 'origin' (y/n)? " yn
            if [ "$yn" != "y" -a "$yn" != "Y" ]; then
                echo "check interrupted"
                exit 1
            fi

            git checkout -b "$branch"
            git push origin "$branch"
            popd >/dev/null
            echo "$line" ; echo
            continue
        fi
        echo
        echo "$line" ; echo
        popd >/dev/null
        verified="y"
    done
done
popd >/dev/null
echo

echo "====  CHECK COMPLETED WITHOUT ERRORS  $doubleline"
exit 0
