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
Module :mod:`openquake.hazardlib.scalerel.leonard2014` implements
:class:`Leonard2010_SCR`
:class:`Leonard2010_SCR_M0`
:class:`Leonard2010_SCR_MX`
"""
import math
import numpy as np
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


class Leonard2010(BaseMSRSigma, BaseASRSigma):
    """
    Leonard, M. (2010). Earthquake fault scaling: self-consistent relating
    of rupture length, width, average displacement and moment release.
    Bulletin of the Seismological Society of America, 100(5A), 1971-1988.

    Bilinear magnitude-to-rupture-length relations for interplate dip-slip
    (normal and reverse) faults, with average displacement derived from the
    rupture length as ``AD = 1.7e-5 * L`` (``L`` in metres).  Added for PR-2
    of the oq-engine integration plan as the ``LEONARD2010`` scaling relation
    of the FDHA distributed-displacement model (Visini et al., 2025); it is
    additive to the stable-continental-region classes above.
    """

    SIGMA_L = 0.23  # log10 standard deviation of rupture length

    def get_median_area(self, mag, rake):
        """Return median rupture area (km^2) for moment ``mag``."""
        length = self.get_rupture_length(mag)
        return length * self._width_from_length(length)

    def get_std_dev_area(self, mag, rake):
        """Return the log10 standard deviation of rupture area."""
        return self.SIGMA_L

    def get_median_mag(self, area, rake):
        """Return median moment magnitude for rupture ``area`` (km^2)."""
        area = np.asarray(area)
        thresh = 1.95 * math.pow(99.0, 5.0 / 3.0)
        length = np.where(
            area <= thresh, np.power(area / 1.95, 3.0 / 5.0), area / 20.0)
        return np.where(
            length <= 99.0,
            2.0 * (np.log10(length) + 1.9),
            np.log10(length) + 4.7)

    def get_std_dev_mag(self, area, rake):
        """Return the log10 standard deviation of moment magnitude."""
        return self.SIGMA_L

    def _width_from_length(self, length):
        width = 1.95 * np.power(length, 2.0 / 3.0)
        return np.where(width > 20.0, 20.0, width)

    def get_rupture_length(self, mag, return_sigma=False):
        """Return rupture length (km) for moment ``mag``."""
        mag = np.asarray(mag)
        log_l = np.where(mag <= 7.1, 0.5 * mag - 1.9, mag - 4.7)
        length = np.power(10.0, log_l)
        if return_sigma:
            return length, self.SIGMA_L
        return length

    def get_average_displacement(self, mag, style=None, return_sigma=False):
        """Return average displacement (m) for moment ``mag``."""
        length_km = np.asarray(self.get_rupture_length(mag))
        ad = 1.7e-5 * length_km * 1_000.0
        if return_sigma:
            return ad, self.SIGMA_L
        return ad


