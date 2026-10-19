# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
The codes identifying the source types (i.e. `b'P'` for PointSource).

This module has no dependencies on purpose: it is the single source of
truth for the codes and it can be imported from anywhere, in particular
from `openquake.hazardlib.valid`, without circular imports. The classes
in `openquake.hazardlib.source` take their codes from here.
"""

POINT = b'P'
COLLAPSED_POINT = b'p'
MULTI_POINT = b'M'
AREA = b'A'
SIMPLE_FAULT = b'S'
KITE_FAULT = b'K'
COMPLEX_FAULT = b'C'
CHARACTERISTIC_FAULT = b'X'
NON_PARAMETRIC = b'N'
MULTI_FAULT = b'F'

# the codes accepted by the parameter filter_sourcecodes, as characters
SOURCE_CODES = frozenset(
    code.decode('ascii') for code in
    (POINT, COLLAPSED_POINT, MULTI_POINT, AREA, SIMPLE_FAULT, KITE_FAULT,
     COMPLEX_FAULT, CHARACTERISTIC_FAULT, NON_PARAMETRIC, MULTI_FAULT))

# consistency check with the codes defined by the source classes
# >>> from openquake.hazardlib.source.base import get_code2cls
# >>> {code.decode('ascii') for code in get_code2cls()} == SOURCE_CODES
# True
