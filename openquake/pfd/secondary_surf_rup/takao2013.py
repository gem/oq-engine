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
Module :mod:`openquake.pfd.secondary_surf_rup.takao2013` implements the
model of Takao et al. (2013) in :class:`Takao2013SecondarySR`.

Supported Fault Styles: Reverse and Strike-slip

References
----------
Takao, M., Tsuchiyama, J., Annaka, T., & Kurita, T. (2013). Application of
probabilistic fault displacement hazard analysis in Japan. Journal of Japan
Association for Earthquake Engineering, 13(1), 17-36.
https://doi.org/10.5610/jaee.13.17
"""

import numpy as np
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup


class Takao2013SecondarySR(BaseSecondarySurfRup):
    """
    Implementation of the Takao et al. (2013) model for reverse and strike-slip faults.
    """

    # Coefficients for 500m pixel size from Takao et al. (2013)
    COEFFS = {
        500: {'C1': -3.839, 'C2': -3.886, 'C3': 0.35, 'C4': 0.2}
    }

    def get_prob(self, r, mag, pixel_size=500):
        """
        Calculates probability of distributed surface rupture for reverse and
        strike-slip faults.

        This model estimates the probability of distributed faulting as a function
        of distance from the principal fault trace and earthquake magnitude.

        :param r:
            Distance to the principal fault trace in km (scalar or array).
        :param mag:
            Earthquake moment magnitude (scalar).
        :param pixel_size:
            Size of the analysis pixel in meters. Currently only 500m is supported.
        :return:
            Probability of distributed surface rupture (0-1).
        """
        # Validate inputs
        if not np.isscalar(mag):
            raise ValueError("mag must be a scalar")

        if pixel_size not in self.COEFFS:
            raise ValueError(
                f"Invalid pixel_size '{pixel_size}'. "
                f"Must be one of {list(self.COEFFS)} meters"
            )

        # Get coefficients
        coeffs = self.COEFFS[pixel_size]
        C1, C2, C3, C4 = coeffs['C1'], coeffs['C2'], coeffs['C3'], coeffs['C4']

        # Convert r to array
        r = np.atleast_1d(np.asarray(r, dtype=float))

        # Logistic regression from Takao et al. (2013). Coefficients C2 and
        # C3 are signed such that fx decreases with r (since C2 + C3*mag < 0
        # for the calibrated magnitude range), giving the physically correct
        # behaviour: probability of distributed rupture decreases with
        # distance from the principal trace.
        fx = C1 + (C2 + C3 * mag) * np.log(r + C4)
        prob = np.exp(fx) / (1.0 + np.exp(fx))

        return prob.item() if prob.size == 1 else prob