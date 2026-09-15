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
Module :mod:`openquake.pfd.scalerel.wc1994` implements
:class:`WellsCoppersmith1994`.

Wells & Coppersmith (1994) empirical relationships. The original
publication provides a comprehensive set of magnitude-to-geometry
regressions in both directions. This implementation focuses on what is
needed for PFDHA: predicting surface rupture geometry and displacement
from moment magnitude.

Conventions:
- Geometry quantities X ∈ {SRL, RLD, RW, RA} use units km (length/width)
  and km^2 (area). Displacements MD/AD are in meters.
- Forward (X|M): log10(X) = a + b * M. The returned sigma is the standard
  deviation of log10(X).
- Inverse (M|X): M = a + b * log10(X). The returned sigma is the standard
  deviation of M.
- For displacement (MD/AD), both forward and inverse forms are provided.
"""

from __future__ import annotations

from collections import namedtuple
import math
import numpy as np

from .base import BaseMSRSigma, BaseASRSigma

Coeff = namedtuple("Coeff", "a b sigma")  # sigma is the SD of the dependent variable


def _style_from_rake(rake: float) -> str:
    """Return faulting style from rake angle (degrees)."""
    if -45.0 <= rake <= 45.0 or rake >= 135.0 or rake <= -135.0:
        return "strike-slip"
    elif rake > 45.0:
        return "reverse"
    else:
        return "normal"


class WellsCoppersmith1994(BaseMSRSigma, BaseASRSigma):
    """
    Scaling relations of Wells & Coppersmith (1994).

    This class exposes forward (X|M) and inverse (M|X) forms for the geometry
    measures SRL, RLD, RW, RA and for displacement measures AD and MD.
    """

    # -----------------------
    # Table 2A: lengths/width/area vs M (both directions)
    # -----------------------
    # Forward: log10(SRL) = a + b*M
    SRL_fwd = {
        "strike-slip": Coeff(-3.55, 0.74, 0.23),
        "reverse":     Coeff(-2.86, 0.63, 0.20),
        "normal":      Coeff(-2.01, 0.50, 0.21),
        "all":         Coeff(-3.22, 0.69, 0.22),
    }
    # Inverse: M = a + b*log10(SRL)
    SRL_inv = {
        "strike-slip": Coeff(5.16, 1.12, 0.28),
        "reverse":     Coeff(5.00, 1.22, 0.28),
        "normal":      Coeff(4.86, 1.32, 0.34),
        "all":         Coeff(5.08, 1.16, 0.28),
    }

    # Forward: log10(RLD) = a + b*M
    RLD_fwd = {
        "strike-slip": Coeff(-2.57, 0.62, 0.15),
        "reverse":     Coeff(-2.42, 0.58, 0.16),
        "normal":      Coeff(-1.88, 0.50, 0.17),
        "all":         Coeff(-2.44, 0.59, 0.16),
    }
    # Inverse: M = a + b*log10(RLD)
    RLD_inv = {
        "strike-slip": Coeff(4.33, 1.49, 0.24),
        "reverse":     Coeff(4.49, 1.49, 0.26),
        "normal":      Coeff(4.34, 1.54, 0.31),
        "all":         Coeff(4.38, 1.49, 0.26),
    }

    # Forward: log10(RW) = a + b*M
    RW_fwd = {
        "strike-slip": Coeff(-0.76, 0.27, 0.14),
        "reverse":     Coeff(-1.61, 0.41, 0.15),
        "normal":      Coeff(-1.14, 0.35, 0.12),
        "all":         Coeff(-1.01, 0.32, 0.15),
    }
    # Inverse: M = a + b*log10(RW)
    RW_inv = {
        "strike-slip": Coeff(3.80, 2.59, 0.45),
        "reverse":     Coeff(4.37, 1.95, 0.32),
        "normal":      Coeff(4.04, 2.11, 0.31),
        "all":         Coeff(4.06, 2.25, 0.41),
    }

    # Forward: log10(RA) = a + b*M
    RA_fwd = {
        "strike-slip": Coeff(-3.42, 0.90, 0.22),
        "reverse":     Coeff(-3.99, 0.98, 0.26),
        "normal":      Coeff(-2.87, 0.82, 0.22),
        "all":         Coeff(-3.49, 0.91, 0.24),
    }
    # Inverse: M = a + b*log10(RA)
    RA_inv = {
        "strike-slip": Coeff(3.98, 1.02, 0.23),
        "reverse":     Coeff(4.33, 0.90, 0.25),
        "normal":      Coeff(3.93, 1.02, 0.25),
        "all":         Coeff(4.07, 0.98, 0.24),
    }

    # -----------------------
    # Table 2B: displacement vs M (both directions)
    # -----------------------
    # Forward: log10(MD) = a + b*M
    MD_fwd = {
        "strike-slip": Coeff(-7.03, 1.03, 0.34),
        "reverse":     Coeff(-1.84, 0.29, 0.42),        "normal":      Coeff(-5.90, 0.89, 0.38),
        "all":         Coeff(-5.46, 0.82, 0.42),
    }
    # Inverse: M = a + b*log10(MD)
    MD_inv = {
        "strike-slip": Coeff(6.81, 0.78, 0.29),
        "reverse":     Coeff(6.52, 0.44, 0.52),        "normal":      Coeff(6.61, 0.71, 0.34),
        "all":         Coeff(6.69, 0.74, 0.40),
    }

    # Forward: log10(AD) = a + b*M
    AD_fwd = {
        "strike-slip": Coeff(-6.32, 0.90, 0.28),
        "reverse":     Coeff(-0.74, 0.08, 0.38),        "normal":      Coeff(-4.45, 0.63, 0.33),
        "all":         Coeff(-4.80, 0.69, 0.36),
    }
    # Inverse: M = a + b*log10(AD)
    AD_inv = {
        "strike-slip": Coeff(7.04, 0.89, 0.28),
        "reverse":     Coeff(6.64, 0.13, 0.50),        "normal":      Coeff(6.78, 0.65, 0.33),
        "all":         Coeff(6.93, 0.82, 0.39),
    }

    # ------------------------------------------------------------------
    # BaseMSR/ASR interface (by default use forward form for X|M)
    # ------------------------------------------------------------------
    def get_median_area(self, mag: float, rake: float):
        """Median rupture area (km^2) from M using log10(RA) = a + b*M."""
        style = _style_from_rake(rake)
        coeff = self.RA_fwd.get(style, self.RA_fwd["all"])
        log10_A = coeff.a + coeff.b * float(mag)
        return np.power(10.0, log10_A)

    def get_std_dev_area(self, mag: float, rake: float):
        """Sigma of log10(RA) (dimensionless, base-10)."""
        style = _style_from_rake(rake)
        return self.RA_fwd.get(style, self.RA_fwd["all"]).sigma

    def get_median_mag(self, area: float, rake: float):
        """Median M from rupture area using M = a + b*log10(RA)."""
        style = _style_from_rake(rake)
        coeff = self.RA_inv.get(style, self.RA_inv["all"])
        return coeff.a + coeff.b * math.log10(float(area))

    def get_std_dev_mag(self, area: float, rake: float):
        """Sigma of M (magnitude units) for the M|log10(RA) relation."""
        style = _style_from_rake(rake)
        return self.RA_inv.get(style, self.RA_inv["all"]).sigma

    # ------------------------------------------------------------------
    # Geometry wrappers (X|M use forward relations)
    # Sigma returned is the SD of log10(X)
    # ------------------------------------------------------------------
    def get_surface_rupture_length(self, mag: float, style: str = "all", return_sigma: bool = False):
        """Return surface rupture length (km) from magnitude for the given faulting ``style``."""
        coeff = self.SRL_fwd.get(style, self.SRL_fwd["all"])
        log10_L = coeff.a + coeff.b * float(mag)
        L = np.power(10.0, log10_L)
        return (L, coeff.sigma) if return_sigma else L

    def get_subsurface_rupture_length(self, mag: float, style: str = "all", return_sigma: bool = False):
        """Return subsurface rupture length (km) from magnitude for the given faulting ``style``."""
        coeff = self.RLD_fwd.get(style, self.RLD_fwd["all"])
        log10_L = coeff.a + coeff.b * float(mag)
        L = np.power(10.0, log10_L)
        return (L, coeff.sigma) if return_sigma else L

    def get_rupture_width(self, mag: float, style: str = "all", return_sigma: bool = False):
        """Return downdip rupture width (km) from magnitude for the given faulting ``style``."""
        coeff = self.RW_fwd.get(style, self.RW_fwd["all"])
        log10_W = coeff.a + coeff.b * float(mag)
        W = np.power(10.0, log10_W)
        return (W, coeff.sigma) if return_sigma else W

    def get_rupture_area(self, mag: float, style: str = "all", return_sigma: bool = False):
        """Return rupture area (km^2) from magnitude for the given faulting ``style``."""
        coeff = self.RA_fwd.get(style, self.RA_fwd["all"])
        log10_A = coeff.a + coeff.b * float(mag)
        A = np.power(10.0, log10_A)
        return (A, coeff.sigma) if return_sigma else A

    # ------------------------------------------------------------------
    # Displacement wrappers (default fallback to "all" for reverse style)
    # Sigma returned is the SD of log10(D)
    # ------------------------------------------------------------------
    def get_average_displacement(self, mag: float, style: str | None = None, return_sigma: bool = False):
        """Return average displacement (m) from magnitude for the given faulting ``style``."""
        style = style or "all"
        coeff = self.AD_fwd.get(style, self.AD_fwd["all"])
        if style == "reverse":
            coeff = self.AD_fwd["all"]
        log10_AD = coeff.a + coeff.b * float(mag)
        AD = np.power(10.0, log10_AD)
        return (AD, coeff.sigma) if return_sigma else AD

    def get_maximum_displacement(self, mag: float, style: str = "all", return_sigma: bool = False):
        """Return maximum displacement (m) from magnitude for the given faulting ``style``."""
        coeff = self.MD_fwd.get(style, self.MD_fwd["all"])
        if style == "reverse":
            coeff = self.MD_fwd["all"]
        log10_MD = coeff.a + coeff.b * float(mag)
        MD = np.power(10.0, log10_MD)
        return (MD, coeff.sigma) if return_sigma else MD


# Functional wrappers (keep public API parity)
_SR = WellsCoppersmith1994()


def surface_rupture_length(mag, style="all", return_sigma=False):
    """Module-level wrapper for :meth:`WellsCoppersmith1994.get_surface_rupture_length`."""
    return _SR.get_surface_rupture_length(mag, style, return_sigma)


def subsurface_rupture_length(mag, style="all", return_sigma=False):
    """Module-level wrapper for :meth:`WellsCoppersmith1994.get_subsurface_rupture_length`."""
    return _SR.get_subsurface_rupture_length(mag, style, return_sigma)


def rupture_width(mag, style="all", return_sigma=False):
    """Module-level wrapper for :meth:`WellsCoppersmith1994.get_rupture_width`."""
    return _SR.get_rupture_width(mag, style, return_sigma)


def rupture_area(mag, style="all", return_sigma=False):
    """Module-level wrapper for :meth:`WellsCoppersmith1994.get_rupture_area`."""
    return _SR.get_rupture_area(mag, style, return_sigma)


def average_displacement(mag, style=None, return_sigma=False):
    """Module-level wrapper for :meth:`WellsCoppersmith1994.get_average_displacement`."""
    return _SR.get_average_displacement(mag, style, return_sigma)


def maximum_displacement(mag, style="all", return_sigma=False):
    """Module-level wrapper for :meth:`WellsCoppersmith1994.get_maximum_displacement`."""
    return _SR.get_maximum_displacement(mag, style, return_sigma)
