#!/bin/bash
#
# testrpm.sh  Copyright (C) 2017-2019 GEM Foundation
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
    command -v "$1" >/dev/null 2>&1 || { echo >&2 "This script requires '$1' but it isn't available. Aborting."; exit 1; }
}

COPR_REPO=openquake-stable

checkcmd docker

while getopts "r:l" opt; do
    case ${opt} in
      \?)
          echo "Usage: $0 [-l] [-r]"
          echo -e "\\nOptions:\\n\\t-l: test RPM locally\\n\\t-r <reponame>: use a GEM COPR repo provided by <reponame> (default: openquake)"
          exit 0
          ;;
      r)
          COPR_REPO=$OPTARG
          ;;
      l)
          LOCAL=1
          ;;
    esac
done

echo "INFO: Test started"
cd build-rpm/RPMS
if [ "$LOCAL" == "1" ]; then
    if compgen -G "python3-oq-engine*.noarch.rpm"; then
        if ! compgen -G "python3-oq-libs*.x86_64.rpm"; then
            echo "WARNING: python3-oq-libs not found locally. Using the one from $COPR_REPO"
        fi
        docker run --rm -v "$(pwd)":/io -t openquake/base -c "yum install -q -y epel-release && yum install -d1 -y /io/python3-oq-{engine,libs}*.rpm"
    else
        echo -e "ERROR: python3-oq-engine not found locally.\\nPlease run 'helpers/makerpm.sh' first. Aborting."
    fi
else
    docker run --rm -t openquake/base -c "yum install -q -y epel-release && curl -sL https://copr.fedoraproject.org/coprs/gem/${COPR_REPO}/repo/epel-7/gem-${COPR_REPO}-epel-7.repo > /etc/yum.repos.d/gem-${COPR_REPO}-epel-7.repo && yum install -d1 -y python3-oq-engine-worker python3-oq-engine-master"
fi
echo "INFO: Test ended"
