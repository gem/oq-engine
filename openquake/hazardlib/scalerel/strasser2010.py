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
Module :mod:`openquake.hazardlib.scalerel.strasser2010` implements
:class:`StrasserInterface`, :class:`StrasserIntraslab`.

"""
from math import log10
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma


class StrasserInterface(BaseMSRSigma, BaseASRSigma):
    """
    Strasser, Arango and Bommer magnitude -- rupture area relationships for
    interface events.

    See F. O. Strasser, M. C. Arango, and J. J. Bommer Scaling of the Source
    Dimensions of Interface and Intraslab Subduction-zone Earthquakes with
    Moment Magnitude Seismological Research Letters, November/December 2010,
    v. 81, p. 941-950, doi:10.1785/gssrl.81.6.941

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median areas as `10** (a + b*mag)`.
        The values are a function of magnitude. Rake is ignored.

        """
        return 10 ** (-3.476 + 0.952 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for Strasser et al 2010. Magnitude is ignored.
        """
        return 0.304

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area Rake is ignored.

        :param area:
            Area in square km.
        """
        return 4.441 + 0.846 * log10(area)

    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation on the magnitude for the Strasser et al. (2010)
        area relation.
        """
        return 0.286

    def get_median_length(self, mag):
        """
        Get median length of the rupture given moment magnitude
        """
        return 10.0 ** (-2.477 + 0.585 * mag)

    def get_std_dev_length(self, mag):
        """
        Get median length standard deviation of the rupture given moment
        magnitude
        """
        return 0.180

    def get_median_width(self, mag):
        """
        Get median width of the rupture given moment magnitude
        """
        return 10.0 ** (-0.882 + 0.351 * mag)

    def get_std_dev_width(self, mag):
        """
        Get median width standard deviation of the rupture given moment
        magnitude
        """
        return 0.173


class StrasserIntraslab(BaseMSRSigma, BaseASRSigma):
    """
    Strasser, Arango and Bommer magnitude -- rupture area relationships for
    intraslab events.

    See F. O. Strasser, M. C. Arango, and J. J. Bommer Scaling of the Source
    Dimensions of Interface and Intraslab Subduction-zone Earthquakes with
    Moment Magnitude Seismological Research Letters, November/December 2010,
    v. 81, p. 941-950, doi:10.1785/gssrl.81.6.941

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median areas as `10** (a + b*mag)`.
        The values are a function of magnitude. Rake is ignored.

        """
        return 10 ** (-3.225 + 0.89 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for Strasser et al 2010. Magnitude is ignored.
        """
        return 0.184

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area Rake is ignored.

        :param area:
            Area in square km.
        """
        return 4.054 + 0.981 * log10(area)

    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation on the magnitude for the Strasser et al. (2010)
        area relation.
        """
        return 0.193
