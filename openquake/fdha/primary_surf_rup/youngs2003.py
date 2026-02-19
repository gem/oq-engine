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
Module :mod:`openquake.fdha.primary_surf_rup.youngs2003` implements
regional models of Youngs et al. (2003) for primary surface rupture.
"""

import numpy as np
from openquake.fdha.primary_surf_rup.base import BasePrimarySurfRup


class Youngs2003Base(BasePrimarySurfRup):
    """
    Base class for Youngs et al. (2003) logistic surface rupture probability
    models. Subclasses set :attr:`coeff_a` and :attr:`coeff_b` (logistic
    regression coefficients).
    """

    coeff_a = None
    coeff_b = None

    def get_prob(self, ctx):
        """
        Compute primary surface rupture probability from magnitude using
        the logistic model P = 1 / (1 + exp(-(a + b * mag))).

        :param ctx:
            Context object with attribute ``mag`` (magnitude, scalar or
            array).
        :returns:
            Probability as float (scalar) or :class:`numpy.ndarray`,
            same shape as ``ctx.mag``.
        """
        m = np.asarray(ctx.mag, dtype=float)
        fx = self.coeff_a + self.coeff_b * m
        prob = 1.0 / (1.0 + np.exp(-fx))
        return prob.item() if prob.shape == () else prob


class Youngs2003PrimarySR_ExC(Youngs2003Base):
    """
    Youngs et al. (2003) primary surface rupture model for Extensional
    Cordillera. Coefficients (a, b) = (-12.53, 1.921); 105 earthquakes,
    Mw 4.5–7.6 (Appendix, p. 25).
    """

    coeff_a = -12.53
    coeff_b = 1.921


class Youngs2003PrimarySR_GB(Youngs2003Base):
    """
    Youngs et al. (2003) primary surface rupture model for Great Basin.
    Coefficients (a, b) = (-16.02, 2.685); 32 earthquakes, Mw 4.9–7.2
    (Appendix, p. 25).
    """

    coeff_a = -16.02
    coeff_b = 2.685


class Youngs2003PrimarySR_nBR(Youngs2003Base):
    """
    Youngs et al. (2003) primary surface rupture model for northern Basin
    and Range. Coefficients (a, b) = (-18.71, 3.041); 47 earthquakes,
    Mw 4.9–7.4 (Appendix, p. 25).
    """

    coeff_a = -18.71
    coeff_b = 3.041
