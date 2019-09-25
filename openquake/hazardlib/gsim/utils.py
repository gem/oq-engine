# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module :mod:`openquake.hazardlib.gsim.utils` contains functions that are common
to several GMPEs.
"""
from openquake.hazardlib.imt import PGA, SA

def mblg_to_mw_johnston_96(mag):
    """
    Convert magnitude value from Mblg to Mw using Johnston 1996 conversion
    equation.

    Implements equation as in line 1654 in hazgridXnga2.f
    """
    return 1.14 + 0.24 * mag + 0.0933 * mag * mag


def mblg_to_mw_atkinson_boore_87(mag):
    """
    Convert magnitude value from Mblg to Mw using Atkinson and Boore 1987
    conversion equation.

    Implements equation as in line 1656 in hazgridXnga2.f
    """
    return 2.715 - 0.277 * mag + 0.127 * mag * mag


def clip_mean(imt, mean):
    """
    Clip GMPE mean value at 1.5 g for PGA and 3 g for short periods
    (0.02 < T < 0.55)
    """
    if imt.period == 0:
        mean[mean > 0.405] = 0.405

    if 0.02 < imt.period < 0.55:
        mean[mean > 1.099] = 1.099

    return mean
