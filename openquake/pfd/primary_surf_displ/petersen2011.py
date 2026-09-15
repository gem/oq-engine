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
Principal fault-displacement model of Petersen et al. (2011) for strike-slip
faults, with bilinear, elliptical, and quadratic along-strike shape variants.

References
----------
Petersen, M.D., et al. (2011). Fault displacement hazard for strike-slip
faults. Bulletin of the Seismological Society of America, 101(2), 805-825.
"""

import numpy as np
from scipy.stats import norm
from openquake.pfd.params import check_choice
from openquake.pfd.primary_surf_displ.base import BasePrimarySurfDispl


class Petersen2011PrimaryFD(BasePrimarySurfDispl):
    """
    Implements the Petersen et al. (2011) primary fault displacement model.

    Model contract: DISPLACEMENT_DEFINITION = "principal",
    DISPLACEMENT_COMPONENT = "lateral" -- Petersen et al. (2011) regress
    principal strike-slip displacement measured as the lateral (horizontal
    fault-parallel) component; Sarmiento et al. (2025, Earthquake Spectra)
    Table 1 lists PEA11 as D_P,L (principal, lateral).

    The along-strike shape variant is selected with the ``version`` model
    parameter ('quadratic' (default), 'bilinear' or 'elliptical') -- pin it
    on the logic-tree branch, e.g.::

        [Petersen2011PrimaryFD]
        version = bilinear

    (all three variants share the same dataset and metric).
    """

    DISPLACEMENT_DEFINITION = "principal"
    DISPLACEMENT_COMPONENT = "lateral"

    _ACCEPTED_VERSIONS = frozenset(["quadratic", "bilinear", "elliptical"])

    def __init__(self, version=None):
        """
        :param version: optional along-strike shape variant pinned by the
            logic-tree branch ('quadratic', 'bilinear' or 'elliptical');
            ``None`` defers to the ``get_prob`` call (legacy default:
            'quadratic').
        """
        super().__init__()
        self.version = check_choice(type(self).__name__, "version", version,
                                    self._ACCEPTED_VERSIONS,
                                    canon=lambda v: str(v).lower())

    def get_prob(self, d, X_L_ratio, mag, version=None):
        """
        Calculate probability of exceeding displacement thresholds [m] for Petersen et al. (2011).
        Supports vectorized inputs: d (n_displacements,), X_L_ratio (n_sites,), mag (scalar or broadcastable).
        Returns array of shape (n_displacements, n_sites).
        """
        # Fall back to the constructor-pinned variant, then legacy default
        if version is None:
            version = self.version if self.version is not None else "quadratic"
        # Prepare inputs
        d_arr = np.atleast_1d(d).astype(float)
        X_L = np.atleast_1d(X_L_ratio).astype(float)
        # Validate X_L_ratio bounds
        if not np.all((X_L >= 0.0) & (X_L <= 1.0)):
            raise ValueError("X_L_ratio must be between 0 and 1")

        # Magnitude: treat scalar or array; flatten for broadcasting
        mag_arr = np.atleast_1d(mag).astype(float)
        if mag_arr.size == 0:
            raise ValueError("Magnitude input is empty")
        # Map version to parameter calculation
        funcs = {
            "bilinear": self.calc_params_bilinear,
            "elliptical": self.calc_params_elliptical,
            "quadratic": self.calc_params_quadratic,
        }
        if version not in funcs:
            raise ValueError(f"Unknown version '{version}' for Petersen et al. (2011)")

        # Compute mu and sigma in ln(cm) units
        # Parameter functions handle broadcasting mag to match X_L
        mu, sd = funcs[version](mag=mag_arr, X_L_ratio=X_L)


        # Convert d to cm and log-space
        d_cm = d_arr * 100.0
        log_d = np.log(d_cm)

        # Reshape for vectorized CDF: (n_displacements, 1) vs (1, n_sites)
        log_d = log_d[:, np.newaxis]           # shape (n_disp, 1)
        mu_mat = mu[np.newaxis, :]             # shape (1, n_sites)
        sd_mat = sd[np.newaxis, :]             # shape (1, n_sites)

        # Compute exceedance probabilities
        prob_exceed = 1.0 - norm.cdf(log_d, loc=mu_mat, scale=sd_mat)
        return prob_exceed

    def calc_params_bilinear(self, mag, X_L_ratio):
        """
        Calculate mean and standard deviation for bilinear model (Eqns 7–9).
        Returns mu and sd arrays matching X_L_ratio shape.
        """
        mag_arr = np.atleast_1d(mag).astype(float)
        X_L = np.atleast_1d(X_L_ratio).astype(float)
        # Broadcast magnitude to match X_L shape
        if mag_arr.shape != X_L.shape:
            mag_arr = np.broadcast_to(mag_arr, X_L.shape)

        # Coefficients (Eqns 7–9)
        a1, b, c1 = 1.7969, 8.5206, -10.2855
        a2, c2 = 1.7658, -7.8962
        sd1, sd2 = 1.2906, 0.9624

        # Intersection
        X_L_prime = (1.0 / b) * ((a2 - a1) * mag_arr + (c2 - c1))
        X_L_prime = np.clip(X_L_prime, 0.25, 0.26)

        # Initialize results
        mu = np.zeros_like(X_L, dtype=float)
        sd = np.zeros_like(X_L, dtype=float)

        # Piecewise
        low_mask = X_L < X_L_prime
        mu[low_mask] = a1 * mag_arr[low_mask] + b * X_L[low_mask] + c1
        sd[low_mask] = sd1
        mu[~low_mask] = a2 * mag_arr[~low_mask] + c2
        sd[~low_mask] = sd2
        return mu, sd

    def calc_params_elliptical(self, mag, X_L_ratio):
        """
        Calculate mean and standard deviation for elliptical model (Eqn 13).
        Returns mu and sd arrays matching X_L_ratio shape.
        """
        mag_arr = np.atleast_1d(mag).astype(float)
        X_L = np.atleast_1d(X_L_ratio).astype(float)
        # Broadcast magnitude
        if mag_arr.shape != X_L.shape:
            mag_arr = np.broadcast_to(mag_arr, X_L.shape)

        # Coefficients
        a, b, c = 1.7927, 3.3041, -11.2192
        sd_val = 1.1348

        # Compute x_star
        x_star = np.sqrt(np.maximum(0.0, 1.0 - (1.0 / 0.5)**2 * (X_L - 0.5)**2))
        mu = b * x_star + a * mag_arr + c
        sd = np.full_like(mu, sd_val)
        return mu, sd

    def calc_params_quadratic(self, mag, X_L_ratio):
        """
        Calculate mean and standard deviation for quadratic model (Eqn 10).
        Returns mu and sd arrays matching X_L_ratio shape.
        """
        mag_arr = np.atleast_1d(mag).astype(float)
        X_L = np.atleast_1d(X_L_ratio).astype(float)
        # Broadcast magnitude
        if mag_arr.shape != X_L.shape:
            mag_arr = np.broadcast_to(mag_arr, X_L.shape)

        # Coefficients
        a, b, c, d = 1.7895, 14.4696, -20.1723, -10.54512
        sd_val = 1.1346

        # Folding
        X_L_fold = np.minimum(X_L, 1.0 - X_L)
        mu = a * mag_arr + b * X_L_fold + c * (X_L_fold ** 2) + d

        sd = np.full_like(mu, sd_val)
        return mu, sd


    def get_prob_D_AD(self, D_AD, X_L_ratio, version="quadratic"):
        """
        Source-defined exceedance probability of normalized D/AD for
        Petersen et al. (2011), Eqs. 14-17. Magnitude is absorbed into AD via
        a separate scaling relation (Wells & Coppersmith 1994 in the source),
        so D/AD has no explicit magnitude dependence here.
        """
        x = np.asarray(X_L_ratio, dtype=float)
        if np.any((x < 0.0) | (x > 1.0)):
            raise ValueError("X_L_ratio must lie in [0, 1]")
        folded = np.minimum(x, 1.0 - x)
        v = str(version).strip().lower()
        if v == "bilinear":  # Eqs. 14-15; (l/L)' = 0.3008.
            mu = np.where(folded < 0.3008,
                          8.2525 * folded - 2.3010, 0.1816)
            sd = np.where(folded < 0.3008, 1.2962, 1.0013)
        elif v == "quadratic":  # Eq. 16.
            mu = 14.2824 * folded - 19.8833 * folded ** 2 - 2.6279
            sd = np.full_like(mu, 1.1419)
        elif v == "elliptical":  # Eq. 17.
            x_star = np.sqrt(np.maximum(0.0, 1.0 - 4.0 * (folded - 0.5) ** 2))
            mu = 3.2699 * x_star - 3.2749
            sd = np.full_like(mu, 1.1419)
        else:
            raise ValueError(
                f"Unknown version '{version}' for get_prob_D_AD; expected "
                f"'bilinear', 'elliptical', or 'quadratic'.")
        return 1.0 - norm.cdf(np.log(np.asarray(D_AD, dtype=float)),
                              loc=mu, scale=sd)
