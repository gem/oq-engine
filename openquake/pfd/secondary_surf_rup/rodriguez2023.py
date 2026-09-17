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
Module :mod:`openquake.pfd.secondary_surf_rup.rodriguez2023` implements
the model of Rodriguez Padilla and Oskin (2023) in :class:`Rodriguez2023SecondarySR`

Supported Fault Styles: Strike-slip only

References
----------
Rodriguez Padilla, A. M., & Oskin, M. E. (2023). Displacement hazard from
distributed ruptures in strike-slip earthquakes. Bulletin of the
Seismological Society of America, 113(6), 2730-2745.
https://doi.org/10.1785/0120230044
"""

import numpy as np
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup


class Rodriguez2023SecondarySR(BaseSecondarySurfRup):
    """
    Implementation of the Rodriguez Padilla and Oskin (2023) model for strike-slip faults.
    """

    # Coefficients for 1m pixel size (median probability)
    COEFFS = {
        1: {'a': 0.13, 'b': 6.7, 'c': -1.19}
    }

    def get_prob(self, r, pixel_size=1):
        """
        Calculates probability of distributed surface rupture for strike-slip faults.

        This model estimates the median probability of distributed faulting as a
        function of distance from the principal fault trace. The model was developed
        for immature strike-slip fault systems.

        :param r:
            Distance to the principal fault trace in km (scalar or array).
        :param pixel_size:
            Size of the analysis pixel in meters. Currently only 1m is supported.
        :return:
            Probability of distributed surface rupture (0-1).
        """
        # Validate pixel_size
        if pixel_size not in self.COEFFS:
            raise ValueError(
                f"Invalid pixel_size '{pixel_size}'. "
                f"This model is only calibrated for pixel_size=1 m."
            )

        # Get coefficients
        coeffs = self.COEFFS[pixel_size]
        a, b, c = coeffs['a'], coeffs['b'], coeffs['c']

        # Convert r to array and from km to metres: Eq. 2 of the paper is
        # nu(x) = nu0 * ((x + x_fr)/x_fr)^-gamma with x and x_fr in metres
        # (Table 1 gives x_fr = 6.7 m for the general model).
        r_m = np.atleast_1d(np.asarray(r, dtype=float)) * 1000.0

        # Compute probability using the power-law model (Eq. 2)
        prob = a * ((r_m + b) / b) ** c

        # Clip probability to valid range [0, 1]
        prob = np.clip(prob, 0.0, 1.0)

        return prob.item() if prob.size == 1 else prob