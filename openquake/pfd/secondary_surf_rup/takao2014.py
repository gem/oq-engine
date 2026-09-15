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
Module :mod:`openquake.pfd.secondary_surf_rup.takao2014` implements
the model of Takao et al. (2014) in :class:`Takao2014SecondarySR`

References
----------
Takao, M., Ueta, K., Annaka, T., Kurita, T., Nakase, H., Kyoya, T., &
Kato, J. (2014). Reliability improvement of probabilistic fault
displacement hazard analysis. Journal of Japan Association for
Earthquake Engineering, 14(2), 16-36. https://doi.org/10.5610/jaee.14.2_16
(in Japanese with English abstract).

An English description of the model (magnitude-independent logistic
regression on ln(r + c3) for 500/250/100/50 m unit cells) is given by
Nishizaka et al. (2026), Seismological Research Letters,
https://doi.org/10.1785/0220250293.
"""

import numpy as np
from openquake.pfd.params import check_positive
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup


class Takao2014SecondarySR(BaseSecondarySurfRup):
    """Implementation of the Takao et al. (2014) model for reverse and strike-slip faults"""

    def __init__(self, pixel_size=None):
        """
        :param pixel_size: optional pixel (cell) size in meters pinned by
            the logic-tree branch; ``None`` defers to the ``get_prob`` call
            (legacy default: 100).
        """
        super().__init__()
        self.pixel_size = check_positive(type(self).__name__, "pixel_size",
                                         pixel_size)

    def get_prob(self, r: float, pixel_size: int = None):
        """
        Calculates probability of surface rupture for reverse and strike-slip faults

        :param r:
            The distance to the principal fault in km
        :param pixel_size:
            Size of the square analysis pixel in meters.
            Valid options are: 500, 250, 100, 50
        :return:
            Probability of surface rupture
        """
        # Fall back to constructor-pinned value, then legacy default
        if pixel_size is None:
            pixel_size = (self.pixel_size
                          if self.pixel_size is not None else 100)
        # Coefficients for different pixel sizes
        coefficients = {
            500: (-3.859, -1.499, 0.2),
            250: (-4.903, -1.459, 0.2),
            100: (-6.135, -1.427, 0.2),
            50: (-6.988, -1.410, 0.2)
        }

        if pixel_size not in coefficients:
            raise ValueError(f"Invalid pixel size. Must be one of {list(coefficients.keys())} meters")

        C1, C2, C3 = coefficients[pixel_size]
        # Logistic regression z = C1 + C2*ln(r + C3); the model is
        # independent of earthquake magnitude (Takao et al., 2014).
        fx = C1 + C2 * np.log(r + C3)
        prob = np.exp(fx) / (1 + np.exp(fx))

        return prob