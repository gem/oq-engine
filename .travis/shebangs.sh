#!/bin/bash
#
# packaging.sh  Copyright (C) 2019 GEM Foundation
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

# shellcheck disable=SC1091
. .travis/common.sh

checkcmd find

find . -not -path '*/\.*' -type f -executable -exec grep -lE '#!.*python$|#!.*python2.*$' '{}' \; | grep -E '.'; test $? -eq 1
