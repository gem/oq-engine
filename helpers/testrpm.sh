#!/bin/bash
#
# makerpm.sh  Copyright (C) 2015-2017 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>

set -e

checkcmd() {
    command -v $1 >/dev/null 2>&1 || { echo >&2 "This script requires '$1' but it isn't available. Aborting."; exit 1; }
}

CUR=$(pwd)
BASE=$(cd $(dirname $0)/.. && /bin/pwd)
COPR_REPO=openquake

checkcmd docker

while (( "$#" )); do
    case "$1" in
        "-h")
            echo "Usage: $0 [-l] [-r]"
            echo -e "\nOptions:\n\t-l: test RPM locally\n\t-r <reponame>: use a GEM COPR repo provided by <reponame> (default: openquake)"
            exit 0
            ;;
        "-r")
            shift
            if [ ! -z $1 ]; then
                COPR_REPO=$1
            else
                echo "ERROR: please provide COPR repo name. Aborting."
            fi
            shift
            ;;
        "-l")
            LOCAL=1
            shift
            ;;
    esac
done

echo "INFO: Test started"
cd build-rpm/RPMS
if [ "$LOCAL" == "1" ]; then
    if [ -f python-oq-engine*.noarch_64.rpm ]; then
        if [ -f python-oq-libs*.x86_64.rpm ]; then
            docker run --rm -v $(pwd):/io -t docker.io/centos:7 bash -c "yum install -q -y epel-release && yum install -y /io/python-oq-engine*.noarch.rpm"
        else
            echo "WARNING: python-oq-libs not found locally. Skipping."
        fi
    else
        echo -e "ERROR: python-oq-engine not found locally.\nPlease run 'helpers/makerpm.sh' first. Aborting."
    fi
else
    docker run --rm -t docker.io/centos:7 bash -c "yum install -q -y epel-release && curl -sL https://copr.fedoraproject.org/coprs/gem/${COPR_REPO}/repo/epel-7/gem-${COPR_REPO}-epel-7.repo > /etc/yum.repos.d/gem-${COPR_REPO}-epel-7.repo && yum install -y python-oq-engine-worker python-oq-engine-master"
fi
echo "INFO: Test ended"
