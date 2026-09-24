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
Module :mod:`openquake.pfd.primary_surf_rup.moss_ross2011` implements the
model of Moss and Ross (2011) in :class:`MossRoss2011PrimarySR`.
"""

import numpy as np
from openquake.pfd.params import check_style
from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup


class MossRoss2011PrimarySR(BasePrimarySurfRup):
    """Principal surface-rupture probability model of Moss and Ross (2011).

    Logistic model of the probability of principal surface rupture for
    reverse-faulting events as a function of magnitude.

    
    Moss, R.E.S., and Ross, Z.E. (2011). Probabilistic fault displacement
    hazard analysis for reverse faults. Bulletin of the Seismological
    Society of America, 101(4), 1542-1553.
    https://doi.org/10.1785/0120100248
    """

    def __init__(self, style=None):
        """
        :param style: optional faulting style declared by the logic-tree
            branch. Moss and Ross (2011) is a reverse-faulting model with a
            single regression; the value does not change the numbers and is
            stored (validated against the global style vocabulary) as a
            declaration of the branch context.
        """
        self.style = check_style(type(self).__name__, style)

    def get_prob(self, mag: float) -> float:
        """
        Model of Moss and Ross (2011) for the probability of surface
        rupture for rupture with reverse rupturing mechanism.

        :param mag:
            The magnitude of the event
        """

        return 1 / (1 + np.exp(7.3 - 1.03 * mag))
