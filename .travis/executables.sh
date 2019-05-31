#!/bin/bash

# shellcheck disable=SC1091
. .travis/common.sh

checkcmd find

find . -not -path '*/\.*' -name \*.py -type f -executable -exec grep  -L 'env python' '{}' \; | grep -E '.'; test $? -eq 1
