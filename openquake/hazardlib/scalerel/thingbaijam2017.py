# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.thingbaijam2017` implements
:class:`Thingbaijam2017_Interface`
:class:`Thingbaijam2017_Crustal`
"""

from numpy import log10
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma


class ThingbaijamInterface(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Implements magnitude-area, area-magnitude,length-magnitude,
    width-magnitude scaling relations.
    """

    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude.
        """
        return 10**(-3.292 + 0.949 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Returns std
        """
        return 0.150

    def get_median_mag(self, area, rake):
        """
        Returns magnitude for a given fault area
        """
        return (log10(area) + 3.292) / 0.949

    def get_std_dev_mag(self, area, rake):
        """
        Returns std
        """
        return 0.150

    def get_median_length(self, mag):
        """
        Get median length of the rupture given moment magnitude
        """
        return 10.0 ** (-2.412 + 0.583 * mag)

    def get_std_dev_length(self, mag):
        """
        Get median length standard deviation of the rupture given moment
        magnitude
        """
        return 0.107

    def get_median_width(self, mag):
        """
        Get median width of the rupture given moment magnitude
        """
        return 10.0 ** (-0.880 + 0.366 * mag)

    def get_std_dev_width(self, mag):
        """
        Get median width standard deviation of the rupture given moment
        magnitude
        """
        return 0.099


class ThingbaijamStrikeSlip(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Implements both magnitude-area and area-magnitude scaling relationships.
    """

    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude.
        """
        return 10**(-3.486 + 0.942 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Returns std
        """
        return 0.184

    def get_median_mag(self, area, rake):
        """
        Returns magnitude for a given fault area
        """
        return (log10(area) + 3.486) / 0.942

    def get_std_dev_mag(self, area, rake):
        """
        Returns std
        """
        return 0.184

    def get_std_dev_width(self, mag):
        """
        Get median width standard deviation of the rupture given moment
        magnitude
        """
        return 0.099


class ThingbaijamNormalFault(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Implements both magnitude-area and area-magnitude scaling relationships.
    """

    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude.
        """
        return 10**(-2.551 + 0.808 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Returns std
        """
        return 0.181

    def get_median_mag(self, area, rake):
        """
        Returns magnitude for a given fault area
        """
        return (log10(area) + 2.551) / 0.808

    def get_std_dev_mag(self, area, rake):
        """
        Returns std
        """
        return 0.181


class ThingbaijamReverseFault(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Implements both magnitude-area and area-magnitude scaling relationships.
    """

    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude.
        """
        return 10**(-4.362 + 1.049 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Returns std
        """
        return 0.121

    def get_median_mag(self, area, rake):
        """
        Returns magnitude for a given fault area
        """
        return (log10(area) + 4.362) / 1.049

    def get_std_dev_mag(self, area, rake):
        """
        Returns std
        """
        return 0.121
