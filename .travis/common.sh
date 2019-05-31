#!/bin/bash
# This file is meant to be sourced

checkcmd() {
    for cmd in "$@"; do
        command -v "$cmd" &> /dev/null || { echo >&2 -e "This script requires '$cmd' but it isn't available. Aborting."; exit 1; }
    done
}
