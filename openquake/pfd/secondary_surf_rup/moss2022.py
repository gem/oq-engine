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
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.pfd.secondary_surf_rup.moss2022` implements
Moss et al. (2022) distributed (secondary) surface rupture probability.

References
----------
Moss, R., Thompson, S., Kuo, C.-H., Younesi, K., and Baumont, D. (2022).
Reverse Fault PFDHA. Report GIRS-2022-05 (Revised 1/17/2024).
DOI: 10.34948/N3F595
"""
import numpy as np
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup

# ── Table 5.3: simple exponential coefficients (85th pct, 500 m grid) ───
# Equation 5.5:  P(d>0) = min(exp(−a·r_km + b), 1)
_COEFF_SIMPLE = {
    'hw': {'a': 2.2, 'b': 0.5},
    'fw': {'a': 2.4, 'b': 0.4},
}

# ── Tables 5.4–5.5: biexponential frequency-CDF coefficients ────────────
# Equation 5.7:  F(x) = a·exp(b·x) + c·exp(d·x),  x in metres
# Equation 5.6:  P = max(1 − F(x), 0)
# Default rows use "exp+random" where available.
_COEFF_BIEXP = {
    'hw': {
        'M7': {'a':  0.6998, 'b':  2.75e-5,  'c': -0.6931, 'd': -0.001219},
        'M6': {'a':  0.8858, 'b':  6.203e-6, 'c': -0.8957, 'd': -0.001959},
        'M5': {'a': 98.45,   'b':  0.0023,   'c': -98.53,  'd': -0.0142},
    },
    'fw': {
        'M7': {'a': 0.1959, 'b': 0.0001,   'c': -0.2020, 'd': -0.0026},
        'M6': {'a': 0.9297, 'b': 2.51e-5,  'c': -0.9233, 'd': -0.002},
    },
}


def _mag_bin(mag):
    """Map magnitude to the bin key used by the biexponential CDF tables."""
    if mag >= 7.0:
        return 'M7'
    if mag >= 6.0:
        return 'M6'
    if mag >= 5.0:
        return 'M5'
    return None


class Moss2022SecondarySR(BaseSecondarySurfRup):
    """
    P(d > 0) for distributed displacement on reverse faults.

    Two methods are available:

    * ``'simple'`` (default) - Eq. 5.5 / Table 5.3 (85th-percentile,
      500 m-grid calibration).
    * ``'biexp'`` - Eqs 5.6–5.7 / Tables 5.4–5.5 (magnitude-binned
      biexponential CDF).

    Distance ``r`` is received in **km** (adapter convention, matching
    ``ctx.r``).  Eq. 5.5 operates in km directly; the biexponential
    CDF (Eq. 5.7) converts to metres internally.
    """

    def get_prob(self, r, rx, mag=None, method="simple", **kwargs):
        """
        Parameters
        ----------
        r : float or array-like
            Distance from the principal fault trace in **km**.
        rx : float or array-like
            Signed cross-fault distance in km.
            Positive = hanging wall, negative = footwall.
        mag : float, optional
            Magnitude (required for ``method='biexp'``).
        method : str
            ``'simple'`` or ``'biexp'``.

        Returns
        -------
        numpy.ndarray or float
            P(d > 0) per site.
        """
        r_arr = np.atleast_1d(np.asarray(r, dtype=float))
        rx_arr = np.atleast_1d(np.asarray(rx, dtype=float))
        hw_mask = rx_arr >= 0

        method_l = method.lower()

        if method_l == 'simple':
            prob = np.where(
                hw_mask,
                np.exp(-_COEFF_SIMPLE['hw']['a'] * r_arr
                       + _COEFF_SIMPLE['hw']['b']),
                np.exp(-_COEFF_SIMPLE['fw']['a'] * r_arr
                       + _COEFF_SIMPLE['fw']['b']),
            )
            prob = np.minimum(prob, 1.0)

        elif method_l == 'biexp':
            if mag is None:
                raise ValueError("mag is required for method='biexp'")
            mbin = _mag_bin(mag)
            if mbin is None:
                return np.zeros_like(r_arr)

            prob = np.zeros_like(r_arr)
            for side_label, mask in [('hw', hw_mask), ('fw', ~hw_mask)]:
                if not np.any(mask):
                    continue
                tbl = _COEFF_BIEXP[side_label]
                if mbin not in tbl:
                    continue
                c = tbl[mbin]
                x = r_arr[mask] * 1000.0               # km → metres for Eq. 5.7
                Fx = (c['a'] * np.exp(c['b'] * x)
                      + c['c'] * np.exp(c['d'] * x))
                prob[mask] = np.clip(1.0 - Fx, 0.0, 1.0)
        else:
            raise ValueError(
                f"Invalid method '{method}'. Accept: simple, biexp")

        return prob.squeeze()
