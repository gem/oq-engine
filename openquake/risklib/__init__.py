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

from openquake.risklib.scientific import (
    VulnerabilityFunction, DegenerateDistribution, classical)

__all__ = ["VulnerabilityFunction", "DegenerateDistribution", "classical"]

__version__ = '0.5.0'

# the following is a hack to discover conflicts with an old version of
# commonlib; it is a transitory trick, and it will be removed in a year
# or so, when the old library will be completely forgotten
import os
try:
    # the module general.py was present in the old library, not in the new one
    from openquake.commonlib import general
except ImportError:
    pass  # you are using the new commonlib, all ok
else:
    raise ImportError(
        'You have an obsolete version of commonlib interfering with the '
        'new one, remove everything in %s' % os.path.dirname(general.__file__))
