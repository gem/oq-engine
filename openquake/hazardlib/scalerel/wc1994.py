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
Module :mod:`openquake.hazardlib.scalerel.wc1994` implements :class:`WC1994`.
"""
from math import log10
from collections import namedtuple
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma


#: coefficient tuple ``log10(Y) = a + b*M`` with log10 standard deviation
#: ``sigma``, used by the FDHA displacement relations (Wells & Coppersmith
#: 1994, Table 2B).
Coeff = namedtuple("Coeff", "a b sigma")


class WC1994(BaseMSRSigma, BaseASRSigma):
    """
    Wells and Coppersmith magnitude -- rupture parameters relationships,
    see 1994, Bull. Seism. Soc. Am., pages 974-2002.

    Implements scaling relationships for:
    - Moment Magnitude (M)
    - Rupture Area (RA)
    - Surface Rupture Length (SRL)
    - Subsurface Rupture Length (RLD)
    - Rupture Width (RW)
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median area from magnitude.

        The values are a function of both magnitude and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param mag:
            Moment magnitude.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if rake is None:
            # their "All" case
            return 10.0 ** (-3.49 + 0.91 * mag)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-3.42 + 0.90 * mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-3.99 + 0.98 * mag)
        else:
            # normal
            return 10.0 ** (-2.87 + 0.82 * mag)

    def get_std_dev_area(self, mag, rake):
        """
        Returns std of the logarithm of rupture area. Magnitude is ignored.
        """
        if rake is None:
            # their "All" case
            return 0.24
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.22
        elif rake > 0:
            # thrust/reverse
            return 0.26
        else:
            # normal
            return 0.22

    def get_median_mag(self, area, rake):
        """
        Calculates median magnitude from area.

        The values are a function of both area and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param area:
            Area in square km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if rake is None:
            # their "All" case
            return 4.07 + 0.98 * log10(area)
        elif (-45 <= rake <= 45) or (rake > 135) or (rake < -135):
            # strike slip
            return 3.98 + 1.02 * log10(area)
        elif rake > 0:
            # thrust/reverse
            return 4.33 + 0.90 * log10(area)
        else:
            # normal
            return 3.93 + 1.02 * log10(area)

    def get_std_dev_mag(self, area, rake):
        """
        Returns std for magnitude. Area is ignored.
        """
        if rake is None:
            # their "All" case
            return 0.24
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.23
        elif rake > 0:
            # thrust/reverse
            return 0.25
        else:
            # normal
            return 0.25

    def get_median_srl(self, mag, rake):
        """
        Calculates median surface rupture length from magnitude.

        The values are a function of both magnitude and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param mag:
            Moment magnitude.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if rake is None:
            # their "All" case
            return 10.0 ** (-3.22 + 0.69 * mag)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-3.55 + 0.74 * mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-2.86 + 0.63 * mag)
        else:
            # normal
            return 10.0 ** (-2.01 + 0.50 * mag)

    def get_std_dev_srl(self, mag, rake):
        """
        Returns std of the logarithm of surface rupture length. Magnitude is ignored.
        """
        if rake is None:
            # their "All" case
            return 0.22
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.23
        elif rake > 0:
            # thrust/reverse
            return 0.20
        else:
            # normal
            return 0.21

    def get_median_mag_from_srl(self, srl, rake):
        """
        Calculates median magnitude from surface rupture length.

        The values are a function of both surface rupture length and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param srl:
            Surface rupture length in km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if rake is None:
            # their "All" case
            return 5.08 + 1.16 * log10(srl)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 5.16 + 1.12 * log10(srl)
        elif rake > 0:
            # thrust/reverse
            return 5.00 + 1.22 * log10(srl)
        else:
            # normal
            return 4.86 + 1.32 * log10(srl)

    def get_std_dev_mag_from_srl(self, srl, rake):
        """
        Returns std for magnitude. Surface rupture length is ignored.
        """
        if rake is None:
            # their "All" case
            return 0.28
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.28
        elif rake > 0:
            # thrust/reverse
            return 0.28
        else:
            # normal
            return 0.34

    def get_median_rld(self, mag, rake):
        """
        Calculates median subsurface rupture length from magnitude.

        The values are a function of both magnitude and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param mag:
            Moment magnitude.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if rake is None:
            # their "All" case
            return 10.0 ** (-2.44 + 0.59 * mag)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-2.57 + 0.62 * mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-2.42 + 0.58 * mag)
        else:
            # normal
            return 10.0 ** (-1.88 + 0.50 * mag)

    def get_std_dev_rld(self, mag, rake):
        """
        Returns std of the logarithm of subsurface rupture length. Magnitude is ignored.
        """
        if rake is None:
            # their "All" case
            return 0.16
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.15
        elif rake > 0:
            # thrust/reverse
            return 0.16
        else:
            # normal
            return 0.17

    def get_median_mag_from_rld(self, rld, rake):
        """
        Calculates median magnitude from subsurface rupture length.

        The values are a function of both subsurface rupture length and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param rld:
            Subsurface rupture length in km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if rake is None:
            # their "All" case
            return 4.38 + 1.49 * log10(rld)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 4.33 + 1.49 * log10(rld)
        elif rake > 0:
            # thrust/reverse
            return 4.49 + 1.49 * log10(rld)
        else:
            # normal
            return 4.34 + 1.54 * log10(rld)

    def get_std_dev_mag_from_rld(self, rld, rake):
        """
        Returns std for magnitude. Subsurface rupture length is ignored.
        """
        if rake is None:
            # their "All" case
            return 0.26
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.24
        elif rake > 0:
            # thrust/reverse
            return 0.26
        else:
            # normal
            return 0.31

    def get_median_rw(self, mag, rake):
        """
        Calculates median rupture width from magnitude.

        The values are a function of both magnitude and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param mag:
            Moment magnitude.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if rake is None:
            # their "All" case
            return 10.0 ** (-1.01 + 0.32 * mag)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 10.0 ** (-0.76 + 0.27 * mag)
        elif rake > 0:
            # thrust/reverse
            return 10.0 ** (-1.61 + 0.41 * mag)
        else:
            # normal
            return 10.0 ** (-1.14 + 0.35 * mag)

    def get_std_dev_rw(self, mag, rake):
        """
        Returns std of the logarithm of rupture width. Magnitude is ignored.
        """
        if rake is None:
            # their "All" case
            return 0.15
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.14
        elif rake > 0:
            # thrust/reverse
            return 0.15
        else:
            # normal
            return 0.12

    def get_median_mag_from_rw(self, rw, rake):
        """
        Calculates median magnitude from rupture width.

        The values are a function of both rupture width and rake.

        Setting the rake to ``None`` causes their "All" rupture-types
        to be applied.

        :param rw:
            Rupture width in km.
        :param rake:
            Rake angle (the rupture propagation direction) in degrees,
            from -180 to 180.
        """
        if rake is None:
            # their "All" case
            return 4.06 + 2.25 * log10(rw)
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 3.80 + 2.59 * log10(rw)
        elif rake > 0:
            # thrust/reverse
            return 4.37 + 1.95 * log10(rw)
        else:
            # normal
            return 4.04 + 2.11 * log10(rw)

    def get_std_dev_mag_from_rw(self, rw, rake):
        """
        Returns std for magnitude. Rupture width is ignored.
        """
        if rake is None:
            # their "All" case
            return 0.41
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return 0.45
        elif rake > 0:
            # thrust/reverse
            return 0.32
        else:
            # normal
            return 0.31

    # ------------------------------------------------------------------
    # FDHA extension: displacement versus magnitude (Table 2B).
    #
    # Added for Probabilistic Fault Displacement Hazard Analysis (PR-2 of
    # the oq-engine integration plan).  Purely additive: the PSHA geometry
    # API above is unchanged and no PSHA code path calls these methods.
    # The relations use the oq-pfdha convention of selecting the rupture
    # style by a ``style`` string, while also accepting a hazardlib ``rake``.
    # ------------------------------------------------------------------
    # Forward: log10(AD) = a + b*M
    AD_fwd = {
        "strike-slip": Coeff(-6.32, 0.90, 0.28),
        "reverse":     Coeff(-0.74, 0.08, 0.38),
        "normal":      Coeff(-4.45, 0.63, 0.33),
        "all":         Coeff(-4.80, 0.69, 0.36),
    }
    # Forward: log10(MD) = a + b*M
    MD_fwd = {
        "strike-slip": Coeff(-7.03, 1.03, 0.34),
        "reverse":     Coeff(-1.84, 0.29, 0.42),
        "normal":      Coeff(-5.90, 0.89, 0.38),
        "all":         Coeff(-5.46, 0.82, 0.42),
    }

    @staticmethod
    def _resolve_style(style, rake):
        """Return the faulting-style key for a ``style``/``rake`` pair."""
        if style is not None:
            return style
        if rake is None:
            return "all"
        if (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            return "strike-slip"
        return "reverse" if rake > 0 else "normal"

    @staticmethod
    def _style_rake(style):
        """Return a representative rake for a faulting-style string.

        Unknown styles (or the aggregate ``"all"``) map to ``None`` so the
        underlying relation falls back to the all-rake coefficients.
        """
        return {
            "strike-slip": 0.0,
            "reverse": 90.0,
            "normal": -90.0,
        }.get(style)

    def get_surface_rupture_length(self, mag, style=None, rake=None,
                                   return_sigma=False):
        """
        Return median surface rupture length (km) from magnitude.

        Signature-compatible wrapper used by the FDHA models: ``style`` may
        be a faulting-style string (``"strike-slip"``, ``"reverse"``,
        ``"normal"``, ``"all"``) instead of a rake angle.
        """
        style = self._resolve_style(style, rake)
        rake = self._style_rake(style)
        value = self.get_median_srl(mag, rake)
        if return_sigma:
            return value, self.get_std_dev_srl(mag, rake)
        return value

    def get_rupture_width(self, mag, style=None, rake=None,
                          return_sigma=False):
        """
        Return median downdip rupture width (km) from magnitude.

        Signature-compatible wrapper used by the FDHA models; see
        :meth:`get_surface_rupture_length` for the ``style`` convention.
        """
        style = self._resolve_style(style, rake)
        rake = self._style_rake(style)
        value = self.get_median_rw(mag, rake)
        if return_sigma:
            return value, self.get_std_dev_rw(mag, rake)
        return value

    def get_average_displacement(self, mag, style=None, rake=None,
                                 return_sigma=False):
        """
        Return median average displacement AD (m) from moment magnitude.

        Wells & Coppersmith (1994) Table 2B, forward form
        ``log10(AD) = a + b*M``.  Following oq-pfdha, the ``"reverse"``
        style falls back to the all-rake relation, because the reverse
        average displacement is not resolved by the 1994 dataset.

        :param return_sigma: if true return ``(AD, sigma)`` where ``sigma``
            is the standard deviation of ``log10(AD)``.
        """
        style = self._resolve_style(style, rake)
        coeff = self.AD_fwd.get(style, self.AD_fwd["all"])
        if style == "reverse":
            coeff = self.AD_fwd["all"]
        ad = 10.0 ** (coeff.a + coeff.b * float(mag))
        return (ad, coeff.sigma) if return_sigma else ad

    def get_maximum_displacement(self, mag, style=None, rake=None,
                                 return_sigma=False):
        """
        Return median maximum displacement MD (m) from moment magnitude.

        Wells & Coppersmith (1994) Table 2B, forward form
        ``log10(MD) = a + b*M``.  As for
        :meth:`get_average_displacement`, the ``"reverse"`` style falls
        back to the all-rake relation.
        """
        style = self._resolve_style(style, rake)
        coeff = self.MD_fwd.get(style, self.MD_fwd["all"])
        if style == "reverse":
            coeff = self.MD_fwd["all"]
        md = 10.0 ** (coeff.a + coeff.b * float(mag))
        return (md, coeff.sigma) if return_sigma else md
    
