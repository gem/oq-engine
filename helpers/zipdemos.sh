#!/bin/bash
#
# zipdemos.sh  Copyright (C) 2017-2019 GEM Foundation
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

if [ -z $1 ]; then echo "Please provide the path where demos are located. Aborting."; exit 1; fi

OQ_DEMOS=$1
checkcmd zip

# Make a zipped copy of each demo
for d in hazard risk; do
    cd ${OQ_DEMOS}/${d}
    echo ${OQ_DEMOS}/${d}
    for z in *; do
        if [ -d $z ]; then zip -q -r ${z}.zip $z; fi
    done
    cd - > /dev/null
done
