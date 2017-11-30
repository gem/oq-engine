#!/bin/bash
set -e
# set -x
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
si_apps="openquakeplatform_standalone $(python -c "from openquakeplatform.settings import STANDALONE_APPS ; print(' '.join(STANDALONE_APPS))")"
si_repos="$(echo "$si_apps" | sed 's/openquakeplatform/oq-platform/g;s/_/-/g')"
for repo in $si_repos; do
    if [ ! -d "../${repo}" ]; then
        cd ..
        read -p "'../${repo}' repository not exists, clone it ? " yn
        git clone "git@github.com:gem/${repo}.git"
        cd -
    fi
    echo "${repo}"
done
echo
