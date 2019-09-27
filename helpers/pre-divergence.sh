#!/bin/bash
#
# pre-divergence.sh  Copyright (C) 2017-2019 GEM Foundation
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

usage () {
    cat <<EOF

$0 <new-engine-version_(maj.min.bugfix)>
    update VM installers links on documentation files with new engine version

$0 <-h|--help>
    this help

EOF
    exit $1
}

#
#  MAIN
#

if [ "$1" = "-h" -o "$1" = "--help" ]; then
    usage 0
fi

if [ $# -ne 1 ]; then
    usage 1
fi

version_new="$1"

files="$(grep -ril 'engine.*[23]\.[0-9]\+\.[0-9]\+' doc/)"
IFS='
'
for f in $files; do
    url_lines="$(grep -ri 'engine.*[23]\.[0-9]\+\.[0-9]\+.[^g][^i][^t]' $f)"
    for url_line in $url_lines; do
        echo "UL:  $url_line"
        url="$(echo "$url_line" | sed 's/.*\(http[^ ]\+\) .*/\1/g')"
        echo "U:   [$url]"
        fex="$(echo "$url" | sed 's@.*/@@g')"
        echo "FEX: [$fex]"
        fex_new="$(echo "$fex" | sed "s/[23]\.[0-9]\+\.[0-9]\+\(.[^g][^i][^t]\)/$version_new\1/g")"
        echo "FNW: [$fex_new]"
        fex_esc="$(echo "$fex" | sed 's/\./\\./g')"
        sed -i "s/$fex_esc/$fex_new/g" $f
    done

echo "F:   $f"
done
