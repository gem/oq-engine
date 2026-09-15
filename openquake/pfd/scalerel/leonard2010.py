# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.pfd.scalerel.leonard2010` implements
:class:`Leonard2010`.

Leonard (2010) self-consistent scaling for dip-slip faults. The model
assumes a constant stress drop and provides bilinear magnitude to
rupture-length relations for interplate normal and reverse faults. Average
displacement is derived from rupture length following the author's
prescription ``AD = 1.7e-5 * L`` where ``L`` is in metres.
"""

from __future__ import annotations

import math
import numpy as np

from .base import BaseMSRSigma, BaseASRSigma


class Leonard2010(BaseMSRSigma, BaseASRSigma):
    """Scaling relations of Leonard (2010)."""

    SIGMA_L = 0.23  # log10 standard deviation for rupture length

    # --- BaseMSR/ASR interface -------------------------------------------------
    def get_median_area(self, mag, rake):
        """Return median rupture area (km^2) for moment ``mag`` (``rake`` unused)."""
        L = self.get_rupture_length(mag)
        if isinstance(L, tuple):
            L = L[0]
        W = self._width_from_length(L)
        return L * W

    def get_std_dev_area(self, mag, rake):
        """Return the log10 standard deviation of rupture area."""
        return self.SIGMA_L

    def get_median_mag(self, area, rake):
        """Return median moment magnitude for rupture ``area`` (km^2; ``rake`` unused)."""
        area = np.asarray(area)
        thresh = 1.95 * math.pow(99.0, 5.0 / 3.0)
        L = np.where(
            area <= thresh,
            np.power(area / 1.95, 3.0 / 5.0),
            area / 20.0,
        )
        mag = np.where(
            L <= 99.0,
            2.0 * (np.log10(L) + 1.9),
            np.log10(L) + 4.7,
        )
        return mag

    def get_std_dev_mag(self, area, rake):
        """Return the log10 standard deviation of moment magnitude."""
        return self.SIGMA_L

    # -------------------------------------------------------------------------
    def _width_from_length(self, length):
        width = 1.95 * np.power(length, 2.0 / 3.0)
        return np.where(width > 20.0, 20.0, width)

    def get_rupture_length(self, mag: float, return_sigma: bool = False):
        """Return rupture length in kilometres for moment ``mag``."""
        mag = np.asarray(mag)
        log_l = np.where(mag <= 7.1, 0.5 * mag - 1.9, mag - 4.7)
        length = np.power(10.0, log_l)
        if return_sigma:
            return length, self.SIGMA_L
        return length

    def get_average_displacement(self, mag: float, style: str | None = None, return_sigma: bool = False):
        """Return average displacement in metres for moment ``mag``."""
        L = self.get_rupture_length(mag)  # km
        if return_sigma:
            if isinstance(L, tuple):
                L, sigma = L
            else:
                sigma = self.SIGMA_L
        L_m = np.asarray(L) * 1_000.0  # convert to metres
        ad = 1.7e-5 * L_m
        if return_sigma:
            return ad, sigma
        return ad


_SR = Leonard2010()


def rupture_length(mag, return_sigma=False):
    """Module-level wrapper for :meth:`Leonard2010.get_rupture_length`."""
    return _SR.get_rupture_length(mag, return_sigma)


def average_displacement(mag, style=None, return_sigma=False):
    """Module-level wrapper for :meth:`Leonard2010.get_average_displacement`."""
    return _SR.get_average_displacement(mag, style, return_sigma)