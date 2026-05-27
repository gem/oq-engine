# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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
:class:`ThingbaijamInterface`
:class:`ThingbaijamStrikeSlip`
:class:`ThingbaijamNormalFault`
:class:`ThingbaijamReverseFault`
"""

from numpy import log10
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma


class ThingbaijamInterface(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Implements moment magnitude-rupture area, rupture area-moment magnitude, 
    rupture length-magnitude, rupture width-magnitude scaling relations 
    for subduction interface.
    """

    def get_median_area(self, mag, rake):
        """Calculates median area from magnitude."""
        return 10**(-3.292 + 0.949 * mag)

    def get_std_dev_area(self, mag, rake):
        """Returns std for rupture area."""
        return 0.150

    def get_median_mag(self, area, rake):
        """Calculates median magnitude from area."""
        return (log10(area) + 3.292) / 0.949

    def get_std_dev_mag(self, area, rake):
        """Returns std for magnitude."""
        return 0.150

    def get_median_length(self, mag):
        """Calculates median length from magnitude."""
        return 10.0 ** (-2.412 + 0.583 * mag)

    def get_std_dev_length(self, mag):
        """Returns std for rupture length."""
        return 0.107

    def get_median_width(self, mag):
        """Calculates median width from magnitude."""
        return 10.0 ** (-0.880 + 0.366 * mag)

    def get_std_dev_width(self, mag):
        """Returns std for rupture width."""
        return 0.099


class ThingbaijamStrikeSlip(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Implements moment magnitude-rupture area, rupture area-moment magnitude, 
    rupture length-magnitude, rupture width-magnitude scaling relations 
    for strike-slip faulting.
    """

    def get_median_area(self, mag, rake):
        """Calculates median area from magnitude."""
        return 10**(-3.486 + 0.942 * mag)

    def get_std_dev_area(self, mag, rake):
        """Returns std for rupture area."""
        return 0.184

    def get_median_mag(self, area, rake):
        """Calculates median magnitude from area."""
        return (log10(area) + 3.486) / 0.942

    def get_std_dev_mag(self, area, rake):
        """Returns std for magnitude."""
        return 0.184
    
    def get_median_length(self, mag):
        """Calculates median length from magnitude."""
        return 10.0 ** (-2.943 + 0.681 * mag)

    def get_std_dev_length(self, mag):
        """RReturns std for rupture length."""
        return 0.151
    
    def get_median_width(self, mag):
        """Calculates median width from magnitude."""
        return 10.0 ** (-0.543 + 0.261 * mag)

    def get_std_dev_width(self, mag):
        """Returns std for rupture width."""
        return 0.105


class ThingbaijamNormalFault(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Implements moment magnitude-rupture area, rupture area-moment magnitude, 
    rupture length-magnitude, rupture width-magnitude scaling relations 
    for normal faulting.
    """

    def get_median_area(self, mag, rake):
        """Calculates median area from magnitude."""
        return 10**(-2.551 + 0.808 * mag)

    def get_std_dev_area(self, mag, rake):
        """Returns std for rupture area."""
        return 0.181

    def get_median_mag(self, area, rake):
        """Calculates median magnitude from area."""
        return (log10(area) + 2.551) / 0.808

    def get_std_dev_mag(self, area, rake):
        """Returns std for magnitude."""
        return 0.181
    
    def get_median_length(self, mag):
        """Calculates median length from magnitude."""
        return 10.0 ** (-1.722 + 0.485 * mag)

    def get_std_dev_length(self, mag):
        """Returns std for rupture length."""
        return 0.128

    def get_median_width(self, mag):
        """Calculates median width from magnitude."""
        return 10.0 ** (-0.829 + 0.323 * mag)

    def get_std_dev_width(self, mag):
        """Returns std for rupture width."""
        return 0.128


class ThingbaijamReverseFault(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Implements moment magnitude-rupture area, rupture area-moment magnitude, 
    rupture length-magnitude, rupture width-magnitude scaling relations 
    for reverse faulting.
    """

    def get_median_area(self, mag, rake):
        """Calculates median area from magnitude."""
        return 10**(-4.362 + 1.049 * mag)

    def get_std_dev_area(self, mag, rake):
        """Returns std for rupture area."""
        return 0.121

    def get_median_mag(self, area, rake):
        """Calculates median magnitude from area."""
        return (log10(area) + 4.362) / 1.049

    def get_std_dev_mag(self, area, rake):
        """Returns std for magnitude."""
        return 0.121

    def get_median_length(self, mag):
        """Calculates median length from magnitude."""
        return 10.0 ** (-2.693 + 0.614 * mag)

    def get_std_dev_length(self, mag):
        """Returns std for rupture length."""
        return 0.083

    def get_median_width(self, mag):
        """Calculates median width from magnitude."""
        return 10.0 ** (-1.669 + 0.435 * mag)

    def get_std_dev_width(self, mag):
        """Returns std for rupture width."""
        return 0.087