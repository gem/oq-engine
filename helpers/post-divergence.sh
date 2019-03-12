#!/bin/bash
#
# post-divergence.sh  Copyright (C) 2017-2019 GEM Foundation
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

$0 <new-engine-stable-branch_(engine-3.x))>
    update documentation files and README.md with links related to the new stable engine branch name

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

branch_new="$1"

clear

# substitute 'blob/master' with 'blob/<stable-branch-name>'
echo "=== Blob/master to blob/$branch_new substitution ==="
echo
files="$(grep -ril 'github.com/gem/oq-engine/blob/master/' README.md doc/)"
IFS='
'
for f in $files; do
    echo "$f"
    sed -i "s@github.com/gem/oq-engine/blob/master/@github.com/gem/oq-engine/blob/$branch_new/@g" "$f"
done
echo
read -p "[Press enter to continue] " a

echo
# show blocks of documentation that must by updated
files="$(grep -ril '<!-- GEM BEGIN:' README.md doc/)"

for f in $files; do
    clear
    echo "=== Show content that must be manually handled  ==="
    echo
    echo "--- FILE: $f ---"
    echo
    sed -n '/<!-- GEM BEGIN[: ].*/,/<!-- GEM END[: ]/p' $f
    echo
    read -p "[Press enter to continue] " a
done
