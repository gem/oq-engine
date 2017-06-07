# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
A Magnitude Frequency Distribution (MFD) is a function that describes the rate
(per year) of earthquakes across all magnitudes.

Package `mfd` contains the basic class for MFD --
:class:`openquake.hazardlib.mfd.base.BaseMFD`, and three actual
implementations:
:class:`openquake.hazardlib.mfd.evenly_discretized.EvenlyDiscretizedMFD`
:class:`openquake.hazardlib.mfd.truncated_gr.TruncatedGRMFD` and
:class:`openquake.hazardlib.mfd.youngs_coppersmith_1985.YoungsCoppersmith1985MFD`.
"""
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.mfd.youngs_coppersmith_1985 import (
    YoungsCoppersmith1985MFD
)
from openquake.hazardlib.mfd.arbitrary_mfd import ArbitraryMFD
from openquake.hazardlib.mfd import multi_mfd
