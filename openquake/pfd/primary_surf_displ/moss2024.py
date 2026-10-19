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
Module :mod:`openquake.pfd.primary_surf_displ.moss2024` implements the
Moss et al. (2024) primary surface fault displacement model.

References
----------
Moss, R. E. S., Thompson, S. C., Kuo, C.-H., Younesi, K., & Baumont, D.
(2024). New probabilistic fault displacement hazard models for reverse
faulting. Earthquake Spectra, 41(4), 2838-2858.
https://doi.org/10.1177/87552930241288560
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
from scipy.interpolate import make_interp_spline
from openquake.pfd.params import check_choice, check_style
from openquake.pfd.primary_surf_displ.base import BasePrimarySurfDispl

class Moss2024PrimaryFD(BasePrimarySurfDispl):
    """
    Model of Moss et al. (2024) for the probability of exceeding
    principal surface fault displacement thresholds [m] on reverse faults.

    ``source='EQS'`` (the default) uses tabulated Earthquake Spectra Table 2
    normalized-displacement alpha/beta parameters. ``source='GIRS'`` uses the
    GIRS-2022-05 Figures 4.3-4.4 gamma-parameter regressions instead. Both
    branches use the same implemented complete/all AD/MD magnitude-scaling
    coefficients from Moss et al. (2024) Table 3 / GIRS-2022-05 Table 4.4. Use
    Moss2022PrimaryFD if you need ``gamma_mode='global'``, the incomplete MD
    subset, or the ``sigma_type`` selector.

    Model contract: DISPLACEMENT_DEFINITION = "principal",
    DISPLACEMENT_COMPONENT = "vertical" -- same principal reverse-fault
    vertical-offset dataset and metric as the GIRS-2022-05 formulation (see
    Moss2022PrimaryFD); Moss et al. (2024, Earthquake Spectra) Tables 2-3.
    """

    DISPLACEMENT_DEFINITION = "principal"
    DISPLACEMENT_COMPONENT = "vertical"

    # Load parameter tables
    path = os.path.dirname(__file__)
    data_dir = os.path.join(path, "data")
    _PARAM_TABLE = {
        "d/ad": pd.read_csv(os.path.join(data_dir,
            "moss_2024_gamma_distribution_parameters_d_ad.csv")),
        "d/md": pd.read_csv(os.path.join(data_dir,
            "moss_2024_gamma_distribution_parameters_d_md.csv")),
    }

    def __init__(self, version=None, source=None, completeness=None,
                 style=None):
        """
        :param version: optional normalization type pinned by the logic-tree
            branch ('AD' or 'MD'); ``None`` defers to the ``get_prob`` call
            (legacy default: 'AD').
        :param source: optional alpha/beta parameter source ('EQS' or
            'GIRS'); legacy default 'EQS'.
        :param completeness: optional reference-model subset ('complete' or
            'all'); legacy default 'all'.
        :param style: optional faulting style declared by the logic-tree
            branch. Moss et al. (2024) is a reverse-faulting model; the value
            does not change the numbers and is stored (validated against the
            global style vocabulary) as a declaration of the branch context.
        """
        self.version = check_choice(type(self).__name__, "version", version,
                                    frozenset(["AD", "MD"]),
                                    canon=lambda v: str(v).upper())
        self.source = check_choice(type(self).__name__, "source", source,
                                   frozenset(["EQS", "GIRS"]),
                                   canon=lambda v: str(v).upper())
        self.completeness = check_choice(
            type(self).__name__, "completeness", completeness,
            frozenset(["complete", "all"]), canon=lambda v: str(v).lower())
        self.style = check_style(type(self).__name__, style)

    def get_prob(self, d, X_L_ratio, mag,
                 version=None, source=None, completeness=None):
        """
        :param d: Target displacement (m), scalar or array-like
        :param X_L_ratio: Normalized position x/L, range [0,1]
        :param mag: Magnitude (scalar)
        :param version: Normalized displacement type, 'AD' or 'MD'
        :param source: Alpha/beta parameter source, 'EQS' or 'GIRS'
        :param completeness: Reference model subset, 'complete' or 'all'
        :returns: Exceedance probability array (same shape as d)
        """

        # Fall back to constructor-pinned values, then legacy defaults
        if version is None:
            version = self.version if self.version is not None else "AD"
        if source is None:
            source = self.source if self.source is not None else "EQS"
        if completeness is None:
            completeness = (self.completeness
                            if self.completeness is not None else "all")

        # --- Validate and map parameters ---
        version_up = version.upper()
        if version_up not in ("AD", "MD"):
            raise ValueError(f"Invalid version '{version}'. Accept: AD, MD")
        internal_version = {"AD": "d/ad", "MD": "d/md"}[version_up]

        source_up = source.upper()
        if source_up not in ("EQS", "GIRS"):
            raise ValueError(f"Invalid source '{source}'. Accept: EQS, GIRS")
        use_girs = (source_up == "GIRS")

        completeness_low = completeness.lower()
        if completeness_low not in ("complete", "all"):
            raise ValueError(f"Invalid completeness '{completeness}'. Accept: complete, all")
        complete_flag = (completeness_low == "complete")

        if not np.isscalar(mag):
            raise ValueError("mag must be a scalar")

        d_arr = np.atleast_1d(d)
        x_arr = np.atleast_1d(X_L_ratio).astype(float)
        if (x_arr < 0).any() or (x_arr > 1).any():
            raise ValueError("X_L_ratio must be between 0 and 1")

        # Symmetric folded position for vector of sites
        folded_x = np.minimum(x_arr, 1 - x_arr)

        # --- Compute α and β (source-defined gamma parameters on D/XD) ---
        alpha, beta = self._gamma_ab(folded_x, internal_version, use_girs)

        # GIRS-2022-05 Table 4.4: MD(M) and AD(M) scaling coefficients.
        if internal_version == "d/ad":
            if complete_flag:
                intercept, slope, sigma_val = -2.87, 0.416, 0.2
            else:
                intercept, slope, sigma_val = -2.98, 0.427, 0.25
        else:  # d/md
            if complete_flag:
                intercept, slope, sigma_val = -2.5, 0.415, 0.2
            else:
                intercept, slope, sigma_val = -2.73, 0.422, 0.35
        mu = intercept + slope * mag
        sigma = sigma_val

        # --- Numerical integration to compute CDF ---
        # ε space [-6,6] with step 0.1
        dz = 0.1
        eps = np.arange(-6.0, 6.0 + dz / 2, dz)
        z = 10 ** (mu + eps * sigma)       # XD = 10^(μ + ε·σ)
        p_eps = stats.norm.pdf(eps)        # PDF of ε

        # Compute CDF of D/XD and weighted average
        y = d_arr[None, :, None] / z[:, None, None]
        cdf_mat = stats.gamma.cdf(y, a=alpha[None, None, :], scale=beta[None, None, :])

        # If MD (D/MD), apply truncation correction
        if internal_version == "d/md":
            c1 = stats.gamma.cdf(1, a=alpha[None, None, :], scale=beta[None, None, :])
            cdf_mat = np.where(y > 1, 1.0, cdf_mat / c1)

        # Weighted accumulation: <cdf> = ∑ (cdf_mat * p_eps) * dz
        cdf = np.tensordot(p_eps, cdf_mat, axes=(0, 0)) * dz

        # Calculate exceedance probability
        prob = 1.0 - cdf

        return prob.squeeze()

    # ------------------------------------------------------------------
    # Source-defined gamma parameters on normalized displacement D/XD.
    # Factored out so the public normalized helpers below share exactly
    # the same alpha/beta computation as get_prob.
    # ------------------------------------------------------------------
    def _gamma_ab(self, folded_x, internal_version, use_girs):
        if use_girs:
            # GIRS-2022-05 Figures 4.3-4.4: x/L gamma regression coefficients.
            if internal_version == "d/ad":
                a1, a2, b1, b2 = 4.2797, 1.6216, -0.5003, 0.5133
            else:
                a1, a2, b1, b2 = 1.422, 1.856, -0.0832, 0.1994
            return a1 * folded_x + a2, b1 * folded_x + b2
        # Moss et al. (2024) Earthquake Spectra, Table 2.
        tab = self._PARAM_TABLE[internal_version]
        f_alpha = make_interp_spline(tab["x_L"], tab["alpha"], k=1)
        f_beta = make_interp_spline(tab["x_L"], tab["beta"], k=1)
        return f_alpha(folded_x), f_beta(folded_x)

    def _validate_version_source(self, version, source):
        version_up = str(version).upper()
        if version_up not in ("AD", "MD"):
            raise ValueError(f"Invalid version '{version}'. Accept: AD, MD")
        source_up = str(source).upper()
        if source_up not in ("EQS", "GIRS"):
            raise ValueError(f"Invalid source '{source}'. Accept: EQS, GIRS")
        return {"AD": "d/ad", "MD": "d/md"}[version_up], source_up == "GIRS"

    def get_prob_D_AD(self, D_AD, X_L_ratio, source="EQS"):
        """
        Source-defined exceedance probability of normalized displacement
        D/AD as a function of x/L. Moss et al. (2024) places a gamma
        distribution on D/AD with x/L-dependent shape and scale parameters
        (alpha, beta). Magnitude does not enter the normalized variable.

        :param D_AD: Normalized displacement D/AD (scalar or array).
        :param X_L_ratio: Normalized along-rupture position in [0, 1]
            (the model folds about 0.5 internally).
        :param source: 'EQS' (Earthquake Spectra Table 2 interpolation;
            default) or 'GIRS' (GIRS-2022-05 Figures 4.3-4.4 regression).
        :returns: Exceedance probability of the same shape as broadcasting
            D_AD against X_L_ratio.
        """
        internal_version, use_girs = self._validate_version_source("AD", source)
        x_arr = np.atleast_1d(X_L_ratio).astype(float)
        if (x_arr < 0).any() or (x_arr > 1).any():
            raise ValueError("X_L_ratio must be between 0 and 1")
        folded_x = np.minimum(x_arr, 1 - x_arr)
        alpha, beta = self._gamma_ab(folded_x, internal_version, use_girs)
        return stats.gamma.sf(np.asarray(D_AD), a=alpha, scale=beta)

    def get_prob_D_MD(self, D_MD, X_L_ratio, source="EQS"):
        """
        Source-defined exceedance probability of normalized displacement
        D/MD as a function of x/L. Moss et al. (2024) places a gamma
        distribution on D/MD truncated to D/MD <= 1 (the maximum
        displacement cannot be exceeded by definition).

        :param D_MD: Normalized displacement D/MD (scalar or array).
        :param X_L_ratio: Normalized along-rupture position in [0, 1].
        :param source: 'EQS' (default) or 'GIRS'.
        :returns: Exceedance probability with the truncation at D/MD = 1
            applied (P(D/MD > y) = 0 for y >= 1).
        """
        internal_version, use_girs = self._validate_version_source("MD", source)
        x_arr = np.atleast_1d(X_L_ratio).astype(float)
        if (x_arr < 0).any() or (x_arr > 1).any():
            raise ValueError("X_L_ratio must be between 0 and 1")
        folded_x = np.minimum(x_arr, 1 - x_arr)
        alpha, beta = self._gamma_ab(folded_x, "d/md", use_girs)
        y = np.asarray(D_MD)
        cdf = stats.gamma.cdf(y, a=alpha, scale=beta)
        c1 = stats.gamma.cdf(1.0, a=alpha, scale=beta)
        cdf = np.where(y > 1, 1.0, cdf / c1)
        return 1.0 - cdf
