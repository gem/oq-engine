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
Module :mod:`openquake.pfd.secondary_surf_rup.ferrario2021` implements the
model of Ferrario and Livio (2021) in :class:`FerrarioLivio2021SecondarySR`.

Supported Fault Styles: Normal only

References
----------
Ferrario, M. F., & Livio, F. (2021). Conditional probability of distributed
surface rupturing during normal-faulting earthquakes. Solid Earth, 12(5),
1197-1209. https://doi.org/10.5194/se-12-1197-2021
"""

import numpy as np
from openquake.pfd.params import check_choice
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup


class FerrarioLivio2021SecondarySR(BaseSecondarySurfRup):
    """
    Implementation of the Ferrario and Livio (2021) model for normal faults.
    """

    # Coefficients for different versions and HW/FW positions
    # From Table 2 in Ferrario and Livio (2021)
    COEFFS = {
        'regular': {
            'HW': {'a': -2.254, 'b': -1.175, 'c': 1.0e-5},
            'FW': {'a': -3.459, 'b': -1.903, 'c': 1.008e-5}
        },
        'conservative': {
            'HW': {'a': -1.888, 'b': -0.8802, 'c': 1.009e-5},
            'FW': {'a': -2.505, 'b': -1.181, 'c': 1.006e-5}
        }
    }

    def __init__(self, version=None):
        """
        :param version: optional variant pinned by the logic-tree branch
            ('regular' or 'conservative'); ``None`` defers to the
            ``get_prob`` call (legacy default: 'regular').
        """
        super().__init__()
        self.version = check_choice(
            type(self).__name__, "version", version,
            frozenset(["regular", "conservative"]),
            canon=lambda v: str(v).lower())

    def get_prob(self, r, rx, version=None):
        """
        Calculates probability of distributed surface rupture for normal faults.

        This model estimates the conditional probability of distributed surface
        rupturing as a function of distance from the principal fault trace,
        calibrated for a 500 x 500 m pixel size.

        :param r:
            Distance to the principal fault trace in km (scalar or array).
        :param rx:
            Horizontal distance to surface projection of fault (scalar or array).
            Positive values indicate hanging wall, negative values indicate footwall.
        :param version:
            Model version. Options are:
            - 'regular': Standard model (default)
            - 'conservative': Conservative estimate with higher probabilities
        :return:
            Probability of distributed surface rupture (0-1).
        """
        # Fall back to constructor-pinned value, then legacy default
        if version is None:
            version = self.version if self.version is not None else "regular"
        # Validate version
        version = version.lower()
        if version not in self.COEFFS:
            raise ValueError(
                f"Invalid version '{version}'. "
                f"Accepted values are: {', '.join(self.COEFFS.keys())}"
            )

        # Convert inputs to arrays
        r = np.atleast_1d(np.asarray(r, dtype=float))
        rx = np.atleast_1d(np.asarray(rx, dtype=float))

        # Broadcast r to match rx shape if scalar
        if r.size == 1 and rx.size > 1:
            r = np.full_like(rx, r.item())
        elif r.shape != rx.shape and r.size > 1:
            raise ValueError("r must be a scalar or have the same shape as rx")

        # Initialize coefficient arrays
        a = np.zeros_like(rx, dtype=float)
        b = np.zeros_like(rx, dtype=float)
        c = np.zeros_like(rx, dtype=float)

        # Masks for hanging wall (rx > 0) and footwall (rx <= 0)
        hw_mask = rx > 0
        fw_mask = ~hw_mask

        # Assign coefficients based on version and position
        coeffs_hw = self.COEFFS[version]['HW']
        coeffs_fw = self.COEFFS[version]['FW']

        a[hw_mask] = coeffs_hw['a']
        b[hw_mask] = coeffs_hw['b']
        c[hw_mask] = coeffs_hw['c']

        a[fw_mask] = coeffs_fw['a']
        b[fw_mask] = coeffs_fw['b']
        c[fw_mask] = coeffs_fw['c']

        # Compute probability using logistic regression
        # Equation from Ferrario and Livio (2021)
        fx = a + b * np.log(r + c)
        prob = np.exp(fx) / (1.0 + np.exp(fx))

        return prob.item() if prob.size == 1 else prob