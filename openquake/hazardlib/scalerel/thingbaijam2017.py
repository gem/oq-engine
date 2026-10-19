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
        """Returns std for rupture length."""
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


#: Per-style crustal classes the dispatcher below delegates to.
_STYLE_CLASSES = {
    "strike-slip": ThingbaijamStrikeSlip,
    "normal": ThingbaijamNormalFault,
    "reverse": ThingbaijamReverseFault,
}

#: Average-displacement (slip) coefficients ``log10(AD) = a + b*M`` for
#: crustal events, Thingbaijam et al. (2017) Table 2.
_SLIP = {
    "strike-slip": (-4.032, 0.558, 0.227),
    "reverse": (-3.156, 0.451, 0.149),
    "normal": (-4.967, 0.693, 0.195),
}


class Thingbaijam2017(BaseMSRSigma, BaseASRSigma):
    """
    Thingbaijam, K. K. S., P. M. Mai, and K. Goda (2017). New Empirical
    Earthquake Source-Scaling Laws. Bulletin of the Seismological Society of
    America, 107(5), pp 2225-2946, doi: 10.1785/0120170017.

    Style-dispatching facade over the crustal ``ThingbaijamStrikeSlip`` /
    ``ThingbaijamNormalFault`` / ``ThingbaijamReverseFault`` relations, with
    the additional average-displacement (slip) relation used by the PFD
    models.  Added for PR-2 of the oq-engine integration plan; it is the
    canonical ``Thingbaijam2017`` name expected by the PFD logic tree and
    reproduces the width rows ``MSR = 2`` of Mammarella et al. (2024)
    Table 1 (see ``openquake/hazardlib/tests/scalerel/pfd_scalerel_test``).
    """

    @staticmethod
    def _style(rake):
        """Return the faulting-style key for a rake angle in degrees."""
        if rake is None:
            return "strike-slip"
        if (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            return "strike-slip"
        return "reverse" if rake > 0 else "normal"

    def _delegate(self, rake):
        return _STYLE_CLASSES[self._style(rake)]()

    def get_median_area(self, mag, rake):
        """Calculates median area from magnitude."""
        return self._delegate(rake).get_median_area(mag, rake)

    def get_std_dev_area(self, mag, rake):
        """Returns std for rupture area."""
        return self._delegate(rake).get_std_dev_area(mag, rake)

    def get_median_mag(self, area, rake):
        """Calculates median magnitude from area."""
        return self._delegate(rake).get_median_mag(area, rake)

    def get_std_dev_mag(self, area, rake):
        """Returns std for magnitude."""
        return self._delegate(rake).get_std_dev_mag(area, rake)

    def get_median_length(self, mag, rake=None, return_sigma=False):
        """Calculates median rupture length (km) from magnitude."""
        cls = self._delegate(rake)
        value = cls.get_median_length(mag)
        if return_sigma:
            return value, cls.get_std_dev_length(mag)
        return value

    def get_std_dev_length(self, mag, rake=None):
        """Returns std for rupture length."""
        return self._delegate(rake).get_std_dev_length(mag)

    def get_median_width(self, mag, rake=None, return_sigma=False):
        """Calculates median rupture width (km) from magnitude."""
        cls = self._delegate(rake)
        value = cls.get_median_width(mag)
        if return_sigma:
            return value, cls.get_std_dev_width(mag)
        return value

    def get_std_dev_width(self, mag, rake=None):
        """Returns std for rupture width."""
        return self._delegate(rake).get_std_dev_width(mag)

    def get_average_displacement(self, mag, style, return_sigma=False):
        """Return median average displacement (m) from moment magnitude."""
        a, b, sigma = _SLIP[style]
        ad = 10.0 ** (a + b * float(mag))
        if return_sigma:
            return ad, sigma
        return ad
