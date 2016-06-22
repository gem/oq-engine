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
Module :mod:`openquake.hazardlib.scalerel.wc1994` implements :class:`WC1994`.
"""
from math import log10
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma


class WC1994(BaseMSRSigma, BaseASRSigma):
    """
    Wells and Coppersmith magnitude -- rupture area relationships,
    see 1994, Bull. Seism. Soc. Am., pages 974-2002.

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of both magnitude and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 10.0 ** (-3.49 + 0.91 * mag)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-3.42 + 0.90 * mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-3.99 + 0.98 * mag)
        else:
            # normal
            return 10.0 ** (-2.87 + 0.82 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for WC1994. Magnitude is ignored.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 0.24
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.22
        elif rake > 0:
            # thrust/reverse
            return 0.26
        else:
            # normal
            return 0.22

    def get_std_dev_mag(self, rake):
        """
        Standard deviation on the magnitude for the WC1994 area relation.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 0.24
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.23
        elif rake > 0:
            # thrust/reverse
            return 0.25
        else:
            # normal
            return 0.25

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        assert rake is None or -180 <= rake <= 180
        if rake is None:
            # their "All" case
            return 4.07 + 0.98 * log10(area)
        elif (-45 <= rake <= 45) or (rake > 135) or (rake < -135):
            # strike slip
            return 3.98 + 1.02 * log10(area)
        elif rake > 0:
            # thrust/reverse
            return 4.33 + 0.90 * log10(area)
        else:
            # normal
            return 3.93 + 1.02 * log10(area)

"""
Local modification of WC1994 to mimic behaviour of GSCFRISK code for the 
Queen Charlotte Strike-Slip (QCSS) fault based on rupture length for the
2015 Seismic Hazard Model of Canada as documented in Adams, J., S. Halchuk, 
T. Allen, and G. Rogers (2015). Canada's 5th Generation seismic hazard model, 
as prepared for the 2015 National Building Code of Canada, 11th Canadian 
Conference on Earthquake Engineering, Victoria, Canada, Paper 93775.
"""
class WC1994_QCSS(BaseMSRSigma):
    """
    Implements magnitude-length scaling relationship for strike-slip faults
    
    Coefficents taken from Table 2A (P990) of Wells, D. L., and K. J. 
    Coppersmith (1994). New empirical relationships among magnitude, 
    rupture length, rupture width, rupture area, and surface displacement, 
    Bull. Seism. Soc. Am. 84, 974-1002.
    
    :param length:
        length for strike slip faults (km)
    :param seis_wid:
        hirdwired seismogenic width of the QCSS (20 km)
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # strike slip
        length = 10.0 ** (-2.57 + 0.67 * mag)
        seis_wid = 20
        
        # estimate area based on length
        if length < seis_wid:
            return length ** 2
        else:
            return length * seis_wid
        

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for WC1994. Magnitude is ignored.
        """
        # strike slip
        return 0.15

