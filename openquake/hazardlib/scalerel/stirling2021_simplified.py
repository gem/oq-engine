# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
Module :mod:`openquake.hazardlib.scalerel.Stirling2021_SimplifiedNZ` implements
:class:`InterfaceLowerEpistemic`, :class:`InterfaceUpperEpistemic`, 
:class:`InterfaceMeanEpistemic`,

"""
from numpy import log10
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma


class InterfaceLowerEpistemic(BaseMSRSigma, BaseASRSigma):
    """
    Simplied Source Scaling Relations for New Zealand NSHM 2022 
    from Stirling et al.2021

    Implements both magnitude-area and area-magnitude scaling relationships.
    
    For subduction interface events:
    Mw = log10A + 3.6 (lower)
    
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median areas as `10** (a + b*mag)`.
        The values are a function of magnitude. Rake is ignored.

        """
        return 10 ** (-3.6 + mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area Rake is ignored.

        :param area:
            Area in square km.
        """
        return 3.6 + log10(area)

    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation is ignored
        """
        return 0.0


class InterfaceUpperEpistemic(BaseMSRSigma, BaseASRSigma):
    """
    Simplied Source Scaling Relations for New Zealand NSHM 2022 
    from Stirling et al.2021

    Implements both magnitude-area and area-magnitude scaling relationships.
    
    For subduction interface events:
    Mw = log10A + 4.1 (upper)
    
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median areas as `10** (a + b*mag)`.
        The values are a function of magnitude. Rake is ignored.

        """
        return 10 ** (-4.1 + mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area Rake is ignored.

        :param area:
            Area in square km.
        """
        return (4.1 + log10(area))

    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation is ignored
        """
        return 0.0
        
        

class InterfaceMeanEpistemic(BaseMSRSigma, BaseASRSigma):
    """
    Simplied Source Scaling Relations for New Zealand NSHM 2022 
    from Stirling et al.2021

    Implements both magnitude-area and area-magnitude scaling relationships.
    
    For subduction interface events:
    Mw = log10A + 3.85 (mean)
    
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median areas as `10** (a + b*mag)`.
        The values are a function of magnitude. Rake is ignored.

        """
        return 10 ** (-3.85 + mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0

    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area Rake is ignored.

        :param area:
            Area in square km.
        """
        return 3.85 + log10(area)

    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation is ignored
        """
        return 0.0

class CrustalLowerEpistemic(BaseMSRSigma, BaseASRSigma):
    """
    Simplied Source Scaling Relations for New Zealand NSHM 2022 
    from Stirling et al.2021
    
    For Strike-slip events:
    Mw = log10A + 3.65 (lower)

    For reverse and normal faulting events:
    Mw = log10A + 3.95 (lower)

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Return magnitude (Mw) given the area and rake.

        :param mag:
            Magnitude in Mw.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-3.65 + mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-3.95 + mag)
        else:
            # normal
            return 10.0 ** (-3.95 + mag)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0


    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area and rake.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if (-45 <= rake <= 45) or (rake > 135) or (rake < -135):
            # strike slip
            return 3.65 + log10(area)
        elif rake > 0:
            # thrust/reverse
            return 3.95 + log10(area)
        else:
            # normal
            return 3.95 + log10(area)

        
    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0
        
        
class CrustalUpperEpistemic(BaseMSRSigma, BaseASRSigma):
    """
    Simplied Source Scaling Relations for New Zealand NSHM 2022 
    from Stirling et al.2021
    
    For Strike-slip events:
    Mw = log10A + 4.3 (upper)

    For reverse and normal faulting events:
     Mw = log10A + 4.3 (upper)

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Return magnitude (Mw) given the area and rake.

        :param mag:
            Magnitude in Mw.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        return 10.0 ** (-4.3 + mag)
        """"
        if (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-4.3 + mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-4.3 + mag)
        else:
            # normal
            return 10.0 ** (-4.3 + mag)
        """

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0


    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area and rake.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        return 4.3 + log10(area)
        """
        if (-45 <= rake <= 45) or (rake > 135) or (rake < -135):
            # strike slip
            return 4.3 + log10(area)
        elif rake > 0:
            # thrust/reverse
            return 4.3 + log10(area)
        else:
            # normal
            return 4.3 + log10(area)
        """
        
    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0


class CrustalMeanEpistemic(BaseMSRSigma, BaseASRSigma):
    """
    Simplied Source Scaling Relations for New Zealand NSHM 2022 
    from Stirling et al.2021
    
    For Strike-slip events:
    Mw = log10A + 4.0 (mean)

    For reverse and normal faulting events:
    Mw = log10A + 4.13 (mean)

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Return magnitude (Mw) given the area and rake.

        :param mag:
            Magnitude in Mw.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """

        if (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-4.0 + mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-4.13 + mag)
        else:
            # normal
            return 10.0 ** (-4.13 + mag)
 
    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0


    def get_median_mag(self, area, rake):
        """
        Return magnitude (Mw) given the area and rake.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if (-45 <= rake <= 45) or (rake > 135) or (rake < -135):
            # strike slip
            return 4.0 + log10(area)
        elif rake > 0:
            # thrust/reverse
            return 4.13 + log10(area)
        else:
            # normal
            return 4.13 + log10(area)

        
    def get_std_dev_mag(self, area, rake):
        """
        Standard deviation is ignored.
        """
        return 0.0






