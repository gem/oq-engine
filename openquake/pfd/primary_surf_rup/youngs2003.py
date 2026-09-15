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
Module :mod:`openquake.pfd.primary_surf_rup.youngs2003` implements
the model of Youngs et al. (2003) in :class:`Youngs2003PrimarySR`
"""

import numpy as np
from openquake.pfd.params import check_style
from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup

class Youngs2003PrimarySR(BasePrimarySurfRup):
    """
    Youngs et al. (2003) surface rupture probability model.

    Youngs et al. (2003) is calibrated for normal-faulting earthquakes. The
    ``style`` argument preserves the historical XML interface: ``"normal"``
    selects the normal-faulting subset, while ``"all"`` selects the broader
    regional datasets. It is not a generic faulting-style selector.

    The ``"all"`` coefficients (a=-12.51, b=2.053) are the logistic regression
    on the 276 worldwide earthquakes of Wells and Coppersmith (1993); the
    ``"normal"`` coefficients (a=-16.02, b=2.685) are the regression on the
    32 Great Basin earthquakes from the Pezzopane and Dawson (1996) data set.
    Both coefficient pairs are tabulated in the Appendix of Youngs et al.
    (2003) ("Coefficients for Equation 4 shown on Figure 4").

    References
    ----------
    Youngs, R.R., et al. (2003). A methodology for probabilistic fault
    displacement hazard analysis (PFDHA). Earthquake Spectra, 19(1), 191-219.
    https://doi.org/10.1193/1.1542891
    """
    _ACCEPTED_STYLES = frozenset(["all", "normal"])

    def __init__(self, style=None):
        """
        :param style: optional dataset selector pinned by the logic-tree
            branch: 'all' (worldwide regression) or 'normal' (Great Basin
            subset). ``None`` defers the choice to the ``get_prob`` call
            (legacy default: 'all').
        """
        super().__init__()
        self.style = check_style(type(self).__name__, style,
                                 self._ACCEPTED_STYLES)

    def get_prob(self, mag, style=None):
        """
        :param mag: float or array-like, earthquake magnitude(s)
        :param style: string, 'all' regional datasets or 'normal' subset;
            ``None`` falls back to the constructor value, then to 'all'
        :return: probability or array of probabilities
        """
        if style is None:
            style = self.style if self.style is not None else "all"
        m = np.asarray(mag, dtype=float)
        if style == 'all':
            a, b = -12.51, 2.053
        elif style == 'normal':
            a, b = -16.02, 2.685
        else:
            raise ValueError(f"Invalid style '{style}'. Use 'all' or 'normal'.")
        fx = a + b * m
        prob = np.exp(fx) / (1.0 + np.exp(fx))
        return prob.item() if prob.shape == () else prob
