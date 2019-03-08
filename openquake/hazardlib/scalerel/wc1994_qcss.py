# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.wc1994_qcss` implements
:class:`WC1994_QCSS`.
"""
from openquake.hazardlib.scalerel.base import BaseMSRSigma


class WC1994_QCSS(BaseMSRSigma):
    """
    Local modification of WC1994 to mimic behaviour of GSCFRISK code for the 
    Queen Charlotte Strike-Slip (QCSS) fault based on rupture length for the
    2015 Seismic Hazard Model of Canada as documented in Adams, J., S. Halchuk, 
    T. Allen, and G. Rogers (2015). Canada's 5th Generation seismic hazard
    model, as prepared for the 2015 National Building Code of Canada, 11th
    Canadian Conference on Earthquake Engineering, Victoria, Canada, Paper
    93775.

    Implements magnitude-length scaling relationship for strike-slip faults

    Coefficents taken from Table 2A (P990) of Wells, D. L., and K. J. 
    Coppersmith (1994). New empirical relationships among magnitude, 
    rupture length, rupture width, rupture area, and surface displacement, 
    Bull. Seism. Soc. Am. 84, 974-1002.
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # strike slip
        length = 10.0 ** (-2.57 + 0.62 * mag)
        seis_wid = 20.0

        # estimate area based on length
        if length < seis_wid:
            return length ** 2.
        else:
            return length * seis_wid

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for WC1994. Magnitude is ignored.
        """
        # strike slip
        return 0.15
