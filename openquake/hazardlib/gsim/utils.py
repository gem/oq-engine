# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
import numpy as np


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


def get_fault_type_dummy_variables(ctx):
    """
    Get fault type dummy variables, see Table 2, pag 107.
    Fault type (Strike-slip, Normal, Thrust/reverse) is
    derived from rake angle.
    Rakes angles within 30 of horizontal are strike-slip,
    angles from 30 to 150 are reverse, and angles from
    -30 to -150 are normal. See paragraph 'Predictor Variables'
    pag 103.
    Note that the 'Unspecified' case is not considered,
    because rake is always given.
    """
    SS = np.zeros_like(ctx.rake)  # strike-slip
    NS = np.zeros_like(ctx.rake)  # normal
    RS = np.zeros_like(ctx.rake)  # reverse
    SS[(np.abs(ctx.rake) <= 30.) | (180. - np.abs(ctx.rake) <= 30.)] = 1.
    RS[(ctx.rake > 30.) & (ctx.rake < 150.)] = 1.
    NS[(ctx.rake > -150.) & (ctx.rake < -30)] = 1.
    return SS, NS, RS
