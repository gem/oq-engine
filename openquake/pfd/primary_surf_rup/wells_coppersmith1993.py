# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
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
Module :mod:`openquake.pfd.primary_surf_rup.wells_coppersmith1993` implements
the model of Wells and Coppersmith (1993) in :class:`WC1993PrimarySR`
"""

import numpy as np
from openquake.pfd.params import check_style
from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup

class WC1993PrimarySR(BasePrimarySurfRup):
    """Principal surface-rupture probability model of Wells and Coppersmith (1993).

    Logistic model of the probability of principal surface rupture as a
    function of magnitude, applicable to all faulting styles.

    References
    ----------
    Wells, D.L., and Coppersmith, K.J. (1993). Likelihood of surface rupture
    as a function of magnitude (abstract). Seismological Research Letters,
    64(1), 54. Coefficients as reported by Youngs et al. (2003), Earthquake
    Spectra, 19(1), 191-219, and Petersen et al. (2011), Bulletin of the
    Seismological Society of America, 101(2), 805-825.
    """

    def __init__(self, style=None):
        """
        :param style: optional faulting style declared by the logic-tree
            branch. This model's single logistic regression covers all
            faulting styles, so the value does not change the numbers; it is
            stored (and validated against the global style vocabulary) as a
            declaration of the branch context.
        """
        super().__init__()
        self.style = check_style(type(self).__name__, style)

    def get_prob(
        self,
        mag: float
    ) -> float:
        """
        Model of Wells and Coppersmith (1993) for the probability of surface
        rupture for rupture with all mechanism.

        :param mag: float or array-like, earthquake magnitude(s)
        :return: probability or array of probabilities
        """
        m = np.asarray(mag, dtype=float)
        fx = -12.51 + 2.053 * m
        prob = np.exp(fx) / (1.0 + np.exp(fx))
        # To handle both single-value and vectorized calls.
        return prob.item() if prob.shape == () else prob