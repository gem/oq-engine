# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.allenhayes2017` implements
:class:`AllenHayesInterface`, :class:`AllenHayesIntraslab`.

"""
from math import log10
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma


class AllenHayesInterfaceLinear(BaseMSRSigma, BaseASRSigma):
    """
    Allen and Hayes Alternative Rupture-Scaling Relationships for Subduction
    Interface and Other Offshore Environments interface events.

    See Bulletin of the Seismological Society of America, Vol. 107, No. 3,
    pp. 1240–1253, June 2017, doi: 10.1785/0120160255

    Implements the linear option for both magnitude-area and area-magnitude
    scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median areas as `10** (a + b*mag)`.
        The values are a function of magnitude. Rake is ignored.

        """
        return 10 ** (-3.63 + 0.96 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for Allen and Hayes 2017. Magnitude and rake
        are ignored.
        """
        return 0.255

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area Rake is ignored.

        :param area:
            Area in square km.
        """
        return (log10(area)+3.63)/0.96

    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation on the magnitude for the Allen and Hayes (2017)
        area relation.
        """
        return 0.266


class AllenHayesInterfaceBilinear(BaseMSRSigma, BaseASRSigma):
    """
    Allen and Hayes Alternative Rupture-Scaling Relationships for Subduction
    Interface and Other Offshore Environments interface events.

    See Bulletin of the Seismological Society of America, Vol. 107, No. 3,
    pp. 1240–1253, June 2017, doi: 10.1785/0120160255

    Implements the bilinear option for both magnitude-area and area-magnitude
    scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median areas as `10** (a + b*mag)`.
        The values are a function of magnitude. Rake is ignored.

        """
        if mag <= 8.63:
            return 10 ** (-5.62 + 1.22 * mag)
        else:
            return 10 ** (2.23 + 0.31 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for Allen and Hayes 2017. Magnitude and rake
        are ignored.
        """
        return 0.256

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area Rake is ignored.

        :param area:
            Area in square km.
        """
        if area <= 74000:
            return (log10(area)+5.62)/1.22
        else:
            return (log10(area)-2.23)/0.31

    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation on the magnitude for the Allen and Hayes (2017)
        area relation.
        """
        return 0.266


class AllenHayesIntraslab(BaseMSRSigma, BaseASRSigma):
    """
    Allen and Hayes Alternative Rupture-Scaling Relationships for Subduction
    Interface and Other Offshore Environments
    interface events.

    See Bulletin of the Seismological Society of America, Vol. 107, No. 3,
    pp. 1240–1253, June 2017, doi: 10.1785/0120160255

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median areas as `10** (a + b*mag)`.
        The values are a function of magnitude. Rake is ignored.

        """
        return 10 ** (-3.89 + 0.96 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for Strasser et al 2010. Magnitude is ignored.
        """
        return 0.19

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area Rake is ignored.

        :param area:
            Area in square km.
        """
        return (log10(area)+3.89)/0.96

    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation on the magnitude for the Strasser et al. (2010)
        area relation.
        """
        return 0.19
