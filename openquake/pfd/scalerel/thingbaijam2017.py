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
Module :mod:`openquake.pfd.scalerel.thingbaijam2017` implements
:class:`ThingbaijamInterface`.

The implementation follows the style of the oq-engine ``hazardlib`` scaling
relations. The regressions of Thingbaijam et al. (2017) relate moment
magnitude to rupture dimensions and average slip for crustal earthquakes.
All relations take the form ``log10(Y) = a + b*M`` with associated
log-space standard deviation ``sigma``.
"""

#from __future__ import annotations

from collections import namedtuple

import numpy as np

from .base import BaseMSRSigma, BaseASRSigma


Coeff = namedtuple("Coeff", "a b sigma")


def _style_from_rake(rake: float) -> str:
    """Return fault style from rake angle."""
    if -45.0 <= rake <= 45.0 or rake >= 135.0 or rake <= -135.0:
        return "strike-slip"
    elif rake > 45.0:
        return "reverse"
    else:
        return "normal"


class ThingbaijamInterface(BaseMSRSigma, BaseASRSigma):
    """Scaling relations of Thingbaijam et al. (2017) for crustal events."""

    # Thingbaijam et al. (2017) - crustal events only
    LENGTH = {
        "strike-slip": Coeff(-2.943, 0.681, 0.151),
        "reverse":     Coeff(-2.693, 0.614, 0.083),
        "normal":      Coeff(-1.722, 0.485, 0.128),
    }

    WIDTH = {
        "strike-slip": Coeff(-0.545, 0.261, 0.105),
        "reverse":     Coeff(-1.669, 0.435, 0.087),
        "normal":      Coeff(-0.829, 0.323, 0.128),
    }

    AREA = {
        "strike-slip": Coeff(-3.486, 0.942, 0.184),
        "reverse":     Coeff(-3.462, 1.049, 0.121),
        "normal":      Coeff(-2.851, 0.808, 0.181),
    }

    SLIP = {
        "strike-slip": Coeff(-4.032, 0.558, 0.227),
        "reverse":     Coeff(-3.156, 0.451, 0.149),
        "normal":      Coeff(-4.967, 0.693, 0.195),
    }

    # --- BaseMSR/ASR interface -------------------------------------------------
    def get_median_area(self, mag, rake):
        """Return median rupture area (km^2) for moment ``mag`` and ``rake``."""
        style = _style_from_rake(rake)
        coeff = self.AREA[style]
        log_a = coeff.a + coeff.b * mag
        return np.power(10.0, log_a)

    def get_std_dev_area(self, mag, rake):
        """Return the log10 standard deviation of rupture area for the ``rake`` style."""
        style = _style_from_rake(rake)
        return self.AREA[style].sigma

    def get_median_mag(self, area, rake):
        """Return median moment magnitude for rupture ``area`` (km^2) and ``rake``."""
        style = _style_from_rake(rake)
        coeff = self.AREA[style]
        return (np.log10(area) - coeff.a) / coeff.b

    def get_std_dev_mag(self, area, rake):
        """Return the log10 standard deviation of moment magnitude for the ``rake`` style."""
        style = _style_from_rake(rake)
        return self.AREA[style].sigma

    # --- Additional helpers ----------------------------------------------------
    def _calc(self, mag: float, coeff: Coeff, return_sigma: bool = False):
        log_y = coeff.a + coeff.b * mag
        value = np.power(10.0, log_y)
        if return_sigma:
            return value, coeff.sigma
        return value

    def get_median_length(self, mag, rake, return_sigma=False):
        """Return median rupture length (km) for moment ``mag`` and ``rake``."""
        style = _style_from_rake(rake)
        return self._calc(mag, self.LENGTH[style], return_sigma)

    def get_median_width(self, mag, rake, return_sigma=False):
        """Return median rupture width (km) for moment ``mag`` and ``rake``."""
        style = _style_from_rake(rake)
        return self._calc(mag, self.WIDTH[style], return_sigma)

    def get_average_displacement(self, mag, style, return_sigma=False):
        """Return median average displacement (m) for moment ``mag`` and faulting ``style``."""
        return self._calc(mag, self.SLIP[style], return_sigma)


# Alias for backward compatibility
Thingbaijam2017 = ThingbaijamInterface

# Functional wrappers ---------------------------------------------------------
_SR = ThingbaijamInterface()


def rupture_length(mag, style, return_sigma=False):
    """Module-level wrapper returning rupture length (km) for ``mag`` and ``style``."""
    rake = 0.0 if style == "strike-slip" else 90.0 if style == "reverse" else -90.0
    return _SR.get_median_length(mag, rake, return_sigma)


def rupture_width(mag, style, return_sigma=False):
    """Module-level wrapper returning rupture width (km) for ``mag`` and ``style``."""
    rake = 0.0 if style == "strike-slip" else 90.0 if style == "reverse" else -90.0
    return _SR.get_median_width(mag, rake, return_sigma)


def rupture_area(mag, style, return_sigma=False):
    """Module-level wrapper returning rupture area (km^2) for ``mag`` and ``style``."""
    rake = 0.0 if style == "strike-slip" else 90.0 if style == "reverse" else -90.0
    value = _SR.get_median_area(mag, rake)
    if return_sigma:
        return value, _SR.get_std_dev_area(mag, rake)
    return value


def average_displacement(mag, style, return_sigma=False):
    """Module-level wrapper returning average displacement (m) for ``mag`` and ``style``."""
    return _SR.get_average_displacement(mag, style, return_sigma)