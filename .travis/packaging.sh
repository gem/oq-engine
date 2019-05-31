#!/bin/bash

# shellcheck disable=SC1091
. .travis/common.sh

checkcmd pip find zipinfo diff

function finish {
  rm -f sources package
}
trap finish EXIT

tmp=$(mktemp -d)

pip wheel --no-deps -w "$tmp" .
find openquake/ -type f ! -name \*.pyc | grep -Ev 'openquake/__init__.py|/tests/|nrml_examples' | sort > sources
zipinfo -1 "$tmp"/openquake.engine*.whl | grep '^openquake/' | grep -v 'nrml_examples' | sort > package
diff -uN sources package
