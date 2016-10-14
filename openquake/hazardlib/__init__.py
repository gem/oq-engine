# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
hazardlib stands for Hazard Library.
"""

from openquake.baselib.general import git_suffix
from openquake.hazardlib import (
    calc, geo, gsim, mfd, scalerel, source, const, correlation, imt, pmf, site,
    tom, near_fault)

# the version is managed by packager.sh with a sed
__version__ = '0.22.0'
__version__ += git_suffix(__file__)
