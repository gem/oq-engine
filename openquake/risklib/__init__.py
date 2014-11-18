# coding=utf-8
# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import sys
from openquake.risklib.scientific import (
    VulnerabilityFunction, DegenerateDistribution, classical)

__all__ = ["VulnerabilityFunction", "DegenerateDistribution", "classical"]

__version__ = '0.5.0'

for path in sys.path:
    if 'oq-commonlib' in path:
        sys.exit('Found an obsolete version of commonlib; '
                 'please remove %s and/or fix your PYTHONPATH' % path)
