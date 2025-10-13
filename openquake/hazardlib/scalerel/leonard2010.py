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
Module :mod:`openquake.hazardlib.scalerel.leonard2014` implements
:class:`Leonard2010_SCR`
:class:`Leonard2010_SCR_M0`
:class:`Leonard2010_SCR_MX`
"""
from numpy import power, log10
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma


class Leonard2010_SCR(BaseMSRSigma, BaseASRSigma):
    """
    Leonard, Mark. "Earthquake fault scaling: Self-consistent relating of rupture 
    length, width, average displacement, and moment release." Bulletin of the 
    Seismological Society of America 100.5A (2010): 1971-1988.

    Implements both magnitude-area and area-magnitude scaling relationships from 
    Table 6, but only for the category SCR
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude.
        """
        #based on table 6 relationship for SCR
        return power(10.0, (mag - 4.19))

    def get_std_dev_area(self, mag, rake):
        """
        Returns zero for now
        """
        return 0.0

    def get_median_mag(self, area, rake):
        """
        Returns magnitude for a given fault area
        """
        #based on table 6 relationship for SCR
        return log10(area) + 4.19

    def get_std_dev_mag(self, area, rake):
        """
        Returns zero for now
        """
        return 0.0


class Leonard2010_SCR_M0(Leonard2010_SCR):
    """
    Leonard, Mark. "Earthquake fault scaling: Self-consistent relating of rupture 
    length, width, average displacement, and moment release." Bulletin of the 
    Seismological Society of America 100.5A (2010): 1971-1988.

    modifies Leonard2010_SCR for a term based on Table 5 and a more precise
    conversion between M0 and Mw
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude.
        """
        #based on table 6 relationship for SCR with modification
        return power(10.0, (mag - 4.22))

    def get_median_mag(self, area, rake):
        """
        Returns magnitude for a given fault area
        """
        #based on table 6 relationship for SCR with modification
        return log10(area) + 4.22


class Leonard2010_SCR_MX(Leonard2010_SCR):
    """
    Modified for specific individual use. NOT RECOMMENDED!
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude.
        """
        #based on table 6 relationship for SCR with modification
        return power(10.0, (mag - 4.00))

    def get_median_mag(self, area, rake):
        """
        Returns magnitude for a given fault area
        """
        #based on table 6 relationship for SCR with modification
        return log10(area) + 4.00


