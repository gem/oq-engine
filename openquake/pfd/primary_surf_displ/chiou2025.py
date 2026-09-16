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
Module :mod:`openquake.pfd.primary_surf_displ.chiou2025` implements
Chiou et al. (2025) primary surface fault displacement model (sum-of-principal)
for strike-slip faults, adapted to the PFDHA API.

This adapter mirrors the API used by other primary surface displacement models:

    get_prob(d, X_L_ratio, mag, style="strike-slip", version="model7")

Behavior and constraints:
- style must be strike-slip (case-insensitive); otherwise a ValueError is raised.
- Recommended magnitude range is (6.0, 8.3). Out-of-range magnitudes emit a warning but are computed.
- The model returns exceedance probabilities for the provided displacement threshold(s).

Coefficients are loaded from
``openquake/pfd/primary_surf_displ/data/chiou_2025_coefficients.csv``.

References
----------
Chiou, B., Chen, R., Thomas, K., Milliner, C., Dawson, T., & Petersen, M.
(2025). Fault displacement model for surface principal rupture of strike-slip
faults. Earthquake Spectra, 41(4), 2746-2782.
https://doi.org/10.1177/87552930251337703
"""

import os
import logging
import numpy as np
from scipy import stats

from openquake.pfd.params import check_style
from openquake.pfd.primary_surf_displ.base import BasePrimarySurfDispl


_LOGGER = logging.getLogger(__name__)


def _load_coefficients() -> np.recarray:
    here = os.path.dirname(__file__)
    data_path = os.path.join(here, "data", "chiou_2025_coefficients.csv")
    # Use numpy genfromtxt to avoid adding pandas dependency here
    arr = np.genfromtxt(
        data_path,
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    return arr


class Chiou2025PrimaryFD(BasePrimarySurfDispl):
    """
    Chiou et al. (2025) primary surface displacement exceedance model
    for sum-of-principal displacement on strike-slip faults.

    Parameters
    ----------
    d : float | array-like
        Target displacement threshold(s) in meters.
    X_L_ratio : float | array-like
        Normalized position x/L in [0, 1]. Supports vectorization over sites.
    mag : float
        Moment magnitude Mw. Recommended range is (6.0, 8.3); outside this
        range a warning is logged and the computation proceeds.
    style : str, optional
        Must be "strike-slip" (case-insensitive). If not, a ValueError is raised.
    version : str, optional
        Model formulation. One of {"model7", "model8.1", "model8.2", "model8.3"}.
        Defaults to "model7".

    Returns
    -------
    np.ndarray
        Exceedance probability(s). Shape follows broadcasting of (n_sites, n_displacements)
        when X_L_ratio is a vector and d is a vector; otherwise reduced appropriately.

    Model contract: DISPLACEMENT_DEFINITION = "sum-of-principal",
    DISPLACEMENT_COMPONENT = "net" -- Chiou et al. (2025, Earthquake
    Spectra, "Fault displacement model for surface principal rupture of
    strike-slip faults") predict displacement summed across the PRINCIPAL
    strands crossed by a profile (distributed ruptures excluded, so the
    secondary slot remains legitimate alongside this model); Sarmiento et
    al. (2025) Table 1 lists CEA25 as D_SP,N* (sum-of-principal,
    pseudo-net component).
    """

    DISPLACEMENT_DEFINITION = "sum-of-principal"
    DISPLACEMENT_COMPONENT = "net"

    # Chiou et al. (2025) define displacement position along their ECS
    # (equivalent continuous surface-rupture) line, so multi-fault ruptures
    # must build the ECS reference line for this model, not the LCP default.
    MULTIFAULT_REFERENCE_LINE = "ecs"

    # cache coefficients at class-level
    _COEFFS = _load_coefficients()

    def __init__(self, version=None, style=None):
        """
        :param version: optional coefficient-set / model-variant identifier
            pinned by the logic-tree branch; ``None`` defers to the
            ``get_prob`` call (legacy default: 'model7').
        :param style: optional faulting style pinned by the logic-tree
            branch; only 'strike-slip' is supported by this model.
        """
        self.version = None if version is None else str(version)
        self.style = check_style(type(self).__name__, style,
                                 frozenset(["strike-slip"]))

    def get_prob(self, d, X_L_ratio, mag, style=None, version=None):
        """Return P(D > d) for the given displacement, position, and magnitude.

        Parameters
        ----------
        d : float or array-like
            Target displacement value(s) in metres.
        X_L_ratio : float or array-like
            Normalized along-strike position (0 to 1).
        mag : float
            Moment magnitude (Mw).
        style : str, optional
            Faulting style; only ``'strike-slip'`` is supported.
        version : str, optional
            Coefficient set / model variant identifier (default ``'model7'``).

        Returns
        -------
        float or ndarray
            Exceedance probability P(D > d | mag, X_L_ratio).

        Raises
        ------
        ValueError
            If ``style`` is not a strike-slip style.
        """
        # Fall back to constructor-pinned values, then legacy defaults
        if style is None:
            style = self.style if self.style is not None else "strike-slip"
        if version is None:
            version = self.version if self.version is not None else "model7"
        # Validate style
        style_str = str(style).strip().lower()
        if style_str not in {"strike-slip", "strikeslip", "ss"}:
            raise ValueError("Chiou2025PrimaryFD only supports style='strike-slip'.")

        # Magnitude check
        m = float(mag)
        if not (6.0 < m < 8.3):
            _LOGGER.warning(
                "Chiou2025PrimaryFD: magnitude %.3f is outside recommended range (6.0, 8.3)",
                m,
            )

        # Version lookup (case-insensitive)
        ver = str(version).strip().lower()
        versions_available = {row[0].lower(): i for i, row in enumerate(self._COEFFS)}
        if ver not in versions_available:
            raise ValueError(
                f"Unknown version '{version}'. Expected one of: {sorted(versions_available.keys())}"
            )
        row = self._COEFFS[versions_available[ver]]

        # Extract coefficients (names align with CSV header)
        c0 = float(row[1])
        m1 = float(row[2])
        m2 = float(row[3])
        m3 = float(row[4])
        c1 = float(row[5])
        cv1 = float(row[6])
        cv2 = float(row[7])
        cv3 = float(row[8])
        cv4 = float(row[9])
        cv5 = float(row[10])
        cn = float(row[11])
        ccap = float(row[12])

        # Inputs
        d_arr = np.atleast_1d(np.asarray(d, dtype=float))  # (n_displ,)
        x_arr = np.atleast_1d(np.asarray(X_L_ratio, dtype=float))  # (n_sites,)
        # Clip X/L to [0,1]
        x_arr = np.clip(x_arr, 0.0, 1.0)

        # Folded x/L in [0, 0.5] using modulus reflection, robust to 1±eps
        r = x_arr - np.floor(x_arr)  # map to [0,1)
        folded_x = 0.5 - np.abs(r - 0.5)  # symmetric fold to [0,0.5]
        # Elliptical x* per author's reference: sqrt(1 - (1/0.5)^2 * (xl - 0.5)^2)
        x_star = np.sqrt(np.maximum(0.0, 1.0 - 4.0 * np.power(x_arr - 0.5, 2.0)))  # (n_sites,)

        # Magnitude scaling f_M(M)
        fm = m2 * (m - m3) + (m2 - m1) / cn * np.log(0.5 * (1.0 + np.exp(-cn * (m - m3))))

        # Mean of Gaussian component
        mu = c0 + fm + c1 * (x_star - 1.0)  # (n_sites,)

        # Aleatory components
        sigma_mag = np.maximum(0.4, cv1 * np.exp(cv2 * np.maximum(0.0, m - 6.1)))
        sigma_xl = cv3 * np.exp(cv4 * np.maximum(0.0, folded_x - ccap))  # (n_sites,)
        sigma_prime = np.sqrt(np.power(sigma_mag, 2.0) + np.power(sigma_xl, 2.0))  # (n_sites,)

        # Exponential mixing parameter and shape for scipy's exponnorm
        nu = cv5
        K = nu / sigma_prime  # (n_sites,)

        # Compute exceedance probabilities using negative EMG (nEMG)
        z = np.log(np.maximum(d_arr, 1e-20))  # (n_displ,)

        # Broadcast to (n_sites, n_displ)
        loc = (-mu)[:, None]
        scale = sigma_prime[:, None]
        K_mat = K[:, None]

        # Using scipy.stats.exponnorm CDF with flipped argument as in reference
        # Author model: prob_exceed = exponnorm.cdf(-ln(d); loc=-mu, scale=sigma', K)
        prob_exceed = stats.exponnorm.cdf(x=(-z)[None, :], loc=loc, scale=scale, K=K_mat)

        # Safety clip
        prob_exceed = np.clip(prob_exceed, 0.0, 1.0)
        return prob_exceed.squeeze()



