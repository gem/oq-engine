# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
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
:class:`nhe.mfd.base.BaseMFD`, and two actual implementations:
:class:`nhe.mfd.evenly_discretized.EvenlyDiscretizedMFD`
and :class:`nhe.mfd.truncated_gr.TruncatedGRMFD`.
"""
from nhe.mfd.evenly_discretized import EvenlyDiscretizedMFD
from nhe.mfd.truncated_gr import TruncatedGRMFD
