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
Module :mod:`openquake.pfd.secondary_surf_rup.youngs2003`
"""

import numpy as np
from openquake.pfd.params import check_choice, check_style
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup


class Youngs2003SecondarySR(BaseSecondarySurfRup):
    """Distributed surface-rupture probability model of Youngs et al. (2003).

    Youngs, R.R., et al. (2003). A methodology for probabilistic fault
    displacement hazard analysis (PFDHA). Earthquake Spectra, 19(1), 191-219.
    """

    def __init__(self, version=None, style=None):
        """
        :param version: optional model-equation variant pinned by the
            logic-tree branch ('1', '2' or '3'; integers are accepted and
            canonicalised to strings); ``None`` defers to the ``get_prob``
            call (legacy default: '3').
        :param style: optional faulting style declared by the logic-tree
            branch. Youngs et al. (2003) secondary regressions carry no
            style selector, so the value does not change the numbers; it is
            stored (validated against the global style vocabulary) as a
            declaration of the branch context.
        """
        self.version = check_choice(type(self).__name__, "version", version,
                                    frozenset(["1", "2", "3"]), canon=str)
        self.style = check_style(type(self).__name__, style)

    def get_prob(self, mag: float, rx: float, r: float, version=None):
            """
            Model of Youngs et al. (2003) for the probability of surface
            rupture for rupture with all rupturing mechanism.
            According to IAEA 1987 PFDHA report, page. 10, section 2.3.3. Distance,
            it says that fault fault displacement hazard, distances are calculated
            as the distance from principal fault strike.
            :param mag:
                The magnitude of the event
            :param rx:
                rx (can be scalar or array of shape (n_sites,))
            :param r:
                The closest distance from the site to surface rupture trace (can be scalar or array of shape (n_sites,))
            :param version:
                The version of the model equation to use. Can be "1", "2", or "3".
                "1": Original model formulation.
                "2": Alternative formulation for average site behavior.
                "3": A 50/50 weighted average of versions "1" and "2" (default).
            """
            # Fall back to constructor-pinned value, then legacy default
            if version is None:
                version = self.version if self.version is not None else "3"
            # Normalize version to string
            version = str(version)

            # Vectorize the hanging wall/footwall determination
            h = np.where(rx > 0., 1, 0)  # Shape (n_sites,) if rx is an array, else scalar

            if version == "1":
                fx = 2.06 + (-4.62 + 0.118 * mag + 0.682 * h) * np.log(np.abs(r + 3.32))
                return np.exp(fx) / (1 + np.exp(fx))
            elif version == "2":
                zi = 0  # average behavior
                fx = 3.27 + (-8.28 + 0.577 * mag + 0.629 * h) * np.log(np.abs(r + 4.14) + 0.611 * zi)
                return np.exp(fx) / (1 + np.exp(fx))
            elif version == "3":
                fx1 = 2.06 + (-4.62 + 0.118 * mag + 0.682 * h) * np.log(np.abs(r + 3.32))
                result1 = np.exp(fx1) / (1 + np.exp(fx1))

                zi = 0  # average behavior
                fx2 = 3.27 + (-8.28 + 0.577 * mag + 0.629 * h) * np.log(np.abs(r + 4.14) + 0.611 * zi)
                result2 = np.exp(fx2) / (1 + np.exp(fx2))

                average_result = 0.5 * result1 + 0.5 * result2
                return average_result