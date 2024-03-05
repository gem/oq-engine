#!/bin/bash
set -e
set -x

which grep sed sort uniq >/dev/null
if [ $? -ne 0 ]; then
    which grep sed sort uniq
fi

NL='
'

usage () {
cat <<EOF

  ./helpers/changelog2ghrel.sh [-c|--check] [<maj.min.bugfix>]
  ./helpers/changelog2ghrel.sh [-h|--help]

    -c                if present checks contributors of current block of
                      changelog 
    <maj.min.bugfix>  if present extracts the block of changelog related
                      to a specific oq-engine release

    -h|--help         this help

  exit with 0 if success, different from 0 if some error occured

EOF
    exit $1
}

per_ver_changelog () {
    version_in="$1"
    
    (
        if [ "$version_in" ]; then
            cat debian/changelog | sed -n "/^python3-oq-engine (${version_in}-.*/,/^python3-oq-engine .*/p"
        else
            cat debian/changelog | sed '/^python3-oq-engine.*/q' | sed '$ d' 
        fi
    )
}

#
#  MAIN
#

perform_check=FALSE
if [ "$1" = "--help" -o "$1" = "-h" ]; then
    usage 0
fi

if [ "$1" = "--check" -o "$1" = "-c" ]; then
    perform_check=TRUE
    shift
fi
version_in="$1"

if [ ! -f debian/changelog ]; then
    usage 1
fi
set +e
LIST_CONTRIB="$(per_ver_changelog "$version_in"| grep '^  \[[^\]*\]$' | sed 's/,/,\n/g' | sed 's/^ \+//g' | sed 's/^\[//g' | sed 's/, *$//g' | sed 's/\] *$//g' | sort | uniq)"
set -e

IFS='
'
for contr in $LIST_CONTRIB; do
    grep -q "${contr}[ \t]\+" CONTRIBUTORS.txt
    if [ $? -ne 0 ]; then
        echo "Contributor '$contr' not found in CONTRIBUTORS.txt"
        exit 1
    fi
done

if [ "$perform_check" = "TRUE" ]; then
    exit 0
fi

IFS='
'
dict_contribs=""
LIST_CONTRIB=$(echo "$LIST_CONTRIB")
for contr in $LIST_CONTRIB; do
    gh_contr="$(grep "^${contr}" CONTRIBUTORS.txt | grep '(@[^)]\+)' | sed 's/.*(@/@/g;s/).*//g')"
        
    dict_contribs="$dict_contribs$contr|$contr ($gh_contr)$NL"
done        

per_ver_changelog "$version_in" | grep -v -- '^ --' | sed '/./b;:n;N;s/\n$//;tn' \
| sed 's/^[a-z][^(]*(\([^\-]\+\).*/## Release \1/g;' | sed 's/^  \(\[.*\]\)/_\1_/g' \
| sed 's/^  //g' > /tmp/changelog2ghrel_$$.txt
echo "$dict_contribs" | sed '/./!d;s/\([^|]*\)|*\(.*\)/s%\1%\2%g/' - | sed -f - /tmp/changelog2ghrel_$$.txt

rm -f /tmp/changelog2ghrel_$$.txt

