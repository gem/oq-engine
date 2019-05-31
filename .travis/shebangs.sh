#!/bin/bash

# shellcheck disable=SC1091
. .travis/common.sh

checkcmd find

find . -not -path '*/\.*' -type f -executable -exec grep -lE '#!.*env python$|python2' '{}' \; | grep -E '.'; test $? -eq 1
