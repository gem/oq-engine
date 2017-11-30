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

