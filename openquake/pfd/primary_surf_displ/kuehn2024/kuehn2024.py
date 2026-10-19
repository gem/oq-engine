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
Module :mod:`openquake.pfd.primary_surf_displ.kuehn2024.kuehn2024`
implements the model of Kuehn et al. (2024) in :class:`Kuehn2024PrimaryFD`.

References
----------
Kuehn, N. M., Kottke, A. R., Sarmiento, A. C., Madugo, C. M., & Bozorgnia,
Y. (2024). A fault displacement model based on the FDHI database. Earthquake
Spectra, 41(4), 2783-2805. https://doi.org/10.1177/87552930241291077
"""


import numpy as np
import pandas as pd
from scipy import stats
from openquake.pfd.params import check_bool, check_style
from openquake.pfd.primary_surf_displ.base import BasePrimarySurfDispl
from openquake.pfd.primary_surf_displ.kuehn2024.load_data import DATA as DATA_COEFFICIENTS



# Model constants
MAG_BREAK = 7.0
DELTA = 0.1

class Kuehn2024PrimaryFD(BasePrimarySurfDispl):
    """Aggregate fault-displacement model of Kuehn et al. (2024), run in the
    principal (primary_surf_displ) slot.

    Bayesian hierarchical model of fault displacement as a function of
    magnitude, normalized along-strike position, and faulting style, with
    optional epistemic-uncertainty sampling over the posterior coefficients.

    References
    ----------
    Kuehn, N. M., Kottke, A. R., Sarmiento, A. C., Madugo, C. M., &
    Bozorgnia, Y. (2024). A fault displacement model based on the FDHI
    database. Earthquake Spectra, 41(4), 2783-2805.
    https://doi.org/10.1177/87552930241291077

    Model contract: DISPLACEMENT_DEFINITION = "aggregate",
    DISPLACEMENT_COMPONENT = "net" -- Kuehn et al. (2024) fit the FDHI
    *aggregate* net displacement (total slip across principal and
    distributed ruptures within the measurement aperture); Sarmiento et al.
    (2025, Earthquake Spectra) Table 1 lists KEA24 under the aggregate
    definition, and there is no cross-definition conversion (ibid.). Because
    the prediction already contains the distributed contribution, the hazard
    kernel runs this model as a single bucket (rate * P_sr * P_fd_aggregate
    * W_p) and any secondary-slot model in the same chain is rejected
    (FDLT-013; docs/design/rupture_location_uncertainty.md, D8).
    """

    DISPLACEMENT_DEFINITION = "aggregate"
    DISPLACEMENT_COMPONENT = "net"

    _ACCEPTED_STYLES = frozenset(["strike-slip", "reverse", "normal"])

    def __init__(self, style=None, epistemic_uncertainty=None, folded=None,
                 coefficient_type=None):
        """
        :param style: optional coefficient-set selector pinned by the
            logic-tree branch ('strike-slip', 'reverse' or 'normal');
            ``None`` defers to the ``get_prob`` call.
        :param epistemic_uncertainty: optional flag pinned by the logic-tree
            branch (accepts booleans or the strings 'true'/'false'); ``None``
            defers to the ``get_prob`` call (legacy default: True).
        :param folded: optional x/L folding flag; legacy default True.
        :param coefficient_type: optional legacy alias ('full' enables
            epistemic uncertainty); ``None`` defers to the call.
        """
        self.style = check_style(type(self).__name__, style,
                                 self._ACCEPTED_STYLES)
        self.epistemic_uncertainty = check_bool(
            type(self).__name__, "epistemic_uncertainty",
            epistemic_uncertainty)
        self.folded = check_bool(type(self).__name__, "folded", folded)
        self.coefficient_type = coefficient_type

    def get_prob(self, d, X_L_ratio, mag, style=None, folded=None,
                 epistemic_uncertainty=None, coefficient_type=None):
        """
        Calculate the probability of exceeding displacement thresholds [m] for Kuehn et al. (2024).
        """
        # Fall back to constructor-pinned values, then legacy defaults
        if style is None:
            style = self.style
        if style is None:
            raise ValueError(
                f"{type(self).__name__}: style must be given either in the "
                f"logic-tree branch or at call time")
        if folded is None:
            folded = self.folded if self.folded is not None else True
        if epistemic_uncertainty is None:
            epistemic_uncertainty = (
                self.epistemic_uncertainty
                if self.epistemic_uncertainty is not None else True)
        if coefficient_type is None:
            coefficient_type = self.coefficient_type
        style = style.lower()
        valid_styles = ['strike-slip', 'reverse', 'normal']
        if style not in valid_styles:
            raise ValueError(f"Invalid style '{style}'. Accepted values are: {', '.join(valid_styles)}")

        # Normalize inputs (allow vectorized X_L_ratio and d)
        mag_arr = np.atleast_1d(mag)
        if mag_arr.size != 1:
            raise ValueError("Only single values allowed for mag")
        current_mag = float(mag_arr[0])
        x_arr = np.atleast_1d(X_L_ratio).astype(float)
        d_arr = np.atleast_1d(d).astype(float)

        # Map coefficient_type if provided
        if coefficient_type is not None:
            ct = str(coefficient_type).lower()
            epistemic_uncertainty = (ct == 'full')

        if epistemic_uncertainty:
            all_coeffs_df = DATA_COEFFICIENTS[style]['full']
            if not isinstance(all_coeffs_df, pd.DataFrame):
                raise TypeError(f"Expected pandas DataFrame for full coefficients for style '{style}'.")

            all_prob_folded = []
            all_prob_site = []

            for _, coeffs_row_series in all_coeffs_df.iterrows():
                # Parameters for position u1 (at x_arr)
                _, lam, mean_site, std_site, _, _ = self._calc_params(
                    coeffs_row_series, current_mag, x_arr, style)
                # Parameters for complementary position u2 (at 1 - x_arr)
                # For folding: calculate at both x and 1-x, then average
                x_comp = 1.0 - x_arr
                _, _, mean_comp, std_comp, _, _ = self._calc_params(
                    coeffs_row_series, current_mag, x_comp, style)

                # Transform displacements (broadcast to (n_displ, n_sites))
                if lam == 0:
                    trans_displ = np.log(d_arr)[:, None]
                else:
                    trans_displ = ((d_arr[:, None] ** lam) - 1.0) / lam

                # Gaussian exceedance, broadcast loc/scale over sites
                prob_site_single = 1.0 - stats.norm.cdf(
                    trans_displ, loc=np.asarray(mean_site)[None, :], scale=np.asarray(std_site)[None, :]
                )
                prob_comp_single = 1.0 - stats.norm.cdf(
                    trans_displ, loc=np.asarray(mean_comp)[None, :], scale=np.asarray(std_comp)[None, :]
                )
                prob_folded_single = 0.5 * (prob_site_single + prob_comp_single)

                all_prob_folded.append(prob_folded_single)
                all_prob_site.append(prob_site_single)

            # Stack along model axis -> (n_models, n_displ, n_sites)
            all_prob_folded_arr = np.stack(all_prob_folded, axis=0)
            all_prob_site_arr = np.stack(all_prob_site, axis=0)

            out = all_prob_folded_arr if folded else all_prob_site_arr
            # If single site, drop the site axis to match historical tests: (n_models, n_displ)
            if x_arr.size == 1 and out.ndim == 3 and out.shape[-1] == 1:
                return out[:, :, 0]
            return out

        else: # Not epistemic_uncertainty
            mean_coeffs_data = DATA_COEFFICIENTS[style]['mean']

            if isinstance(mean_coeffs_data, pd.DataFrame):
                if not mean_coeffs_data.empty:
                    if 'median' in mean_coeffs_data.index:
                        single_coeffs_series = mean_coeffs_data.loc['median']
                    else:
                        single_coeffs_series = mean_coeffs_data.iloc[0]
                else:
                    raise ValueError(
                        f"Mean coefficients DataFrame for style '{style}' is empty."
                    )
            elif isinstance(mean_coeffs_data, pd.Series):
                single_coeffs_series = mean_coeffs_data
            else:
                raise TypeError(
                    f"Mean coefficients for style '{style}' must be a pandas Series or a DataFrame. "
                    f"Got {type(mean_coeffs_data)}."
                )

            if not isinstance(single_coeffs_series, pd.Series):
                 raise TypeError(
                     f"Failed to derive a pandas Series for mean coefficients for style '{style}'. "
                     f"Got type: {type(single_coeffs_series)}."
                 )

            # Parameters at all sites
            _, lam, mean_site, std_site, _, _ = self._calc_params(
                single_coeffs_series, current_mag, x_arr, style
            )
            # Calculate complementary position: simply 1 - x
            # (no symmetric folding - the folded probability averages x and 1-x)
            x_comp = 1.0 - x_arr
            _, _, mean_comp, std_comp, _, _ = self._calc_params(
                single_coeffs_series, current_mag, x_comp, style
            )

            # Transform displacements -> (n_displ, n_sites)
            if lam == 0:
                trans_displ = np.log(d_arr)[:, None]
            else:
                trans_displ = ((d_arr[:, None] ** lam) - 1.0) / lam

            prob_site = 1.0 - stats.norm.cdf(
                trans_displ, loc=np.asarray(mean_site)[None, :], scale=np.asarray(std_site)[None, :]
            )
            prob_comp = 1.0 - stats.norm.cdf(
                trans_displ, loc=np.asarray(mean_comp)[None, :], scale=np.asarray(std_comp)[None, :]
            )
            prob_folded = 0.5 * (prob_site + prob_comp)

            # Select output based on folded parameter
            out = prob_folded if folded else prob_site

            # If single site, return (n_displ,) for backward-compatibility tests
            if x_arr.size == 1 and out.shape[1] == 1:
                return out[:, 0]
            return out.T


    def _calc_params(self, coeffs, mag, X_L_ratio, style):
        style = style.lower()
        func_map = {
            'strike-slip': self._calc_strike_slip,
            'reverse': self._calc_reverse,
            'normal': self._calc_normal}

        return func_map[style](coeffs, mag, X_L_ratio)

    def _calc_strike_slip(self, coeffs, mag, X_L_ratio):
        mu = self._calc_mean(coeffs, mag, X_L_ratio)
        std_mode = self._calc_std_mode_bilinear(coeffs, mag)
        std_within = self._calc_std_within(coeffs, X_L_ratio)

        std_total = np.sqrt(std_mode**2 + std_within**2)

        lam = coeffs['lambda']
        model_id = coeffs.get('model_id', 1)
        return model_id, lam, mu, std_total, std_within, std_mode

    def _calc_normal(self, coeffs, mag, X_L_ratio):
        mu = self._calc_mean(coeffs, mag, X_L_ratio)
        std_mode = self._calc_std_mode_sigmoid(coeffs, mag)

        # Within-event sigma is constant across sites for normal style; vectorize to sites
        sigma_val = float(coeffs['sigma'])
        std_within = np.full(mu.shape, sigma_val, dtype=float)

        std_total = np.sqrt(std_mode**2 + std_within**2)

        lam = coeffs['lambda']
        model_id = coeffs.get('model_id', 1)
        return model_id, lam, mu, std_total, std_within, std_mode


    def _calc_reverse(self, coeffs, mag, X_L_ratio):
        mu = self._calc_mean(coeffs, mag, X_L_ratio)
        std_within = self._calc_std_within(coeffs, X_L_ratio)

        std_mode = float(coeffs['s_m,r'])

        std_total = np.sqrt(std_mode**2 + std_within**2)

        lam = coeffs['lambda']
        model_id = coeffs.get('model_id', 1)
        return model_id, lam, mu, std_total, std_within, std_mode

    # Helper functions now support vectorized X_L_ratio (arrays)
    def _calc_mean(self, coeffs, mag, X_L_ratio):
        mode = self._calc_mode(coeffs, mag)  # scalar
        alpha = float(coeffs['alpha'])
        beta = float(coeffs['beta'])
        gamma = float(coeffs['gamma'])

        x = np.atleast_1d(X_L_ratio).astype(float)

        denom = alpha + beta
        if denom != 0.0:
            term_powers_ab = ((alpha / denom) ** alpha) * ((beta / denom) ** beta)
        else:
            term_powers_ab = 0.0

        a = mode - gamma * term_powers_ab
        term1 = np.power(x, alpha)
        term2 = np.power(1.0 - x, beta)
        mu_val = a + gamma * term1 * term2
        return mu_val

    def _calc_mode(self, coeffs, mag):
        val = (coeffs['c1'] + coeffs['c2'] * (mag - MAG_BREAK) +
               (coeffs['c3'] - coeffs['c2']) * DELTA * np.log(1 + np.exp((mag - MAG_BREAK) / DELTA)))
        return float(np.asarray(val))

    def _calc_std_mode_bilinear(self, coeffs, mag):
        val = (coeffs['s_m,s1'] + coeffs['s_m,s2'] * (mag - coeffs['s_m,s3']) -
               coeffs['s_m,s2'] * DELTA * np.log(1 + np.exp((mag - coeffs['s_m,s3']) / DELTA)))
        return float(np.asarray(val))

    def _calc_std_mode_sigmoid(self, coeffs, mag):
        val = coeffs['s_m,n1'] - coeffs['s_m,n2'] / (1 + np.exp(-coeffs['s_m,n3'] * (mag - MAG_BREAK)))
        return float(np.asarray(val))

    def _calc_std_within(self, coeffs, X_L_ratio):
        s1 = coeffs.get('s_s1', coeffs.get('s_r1'))
        s2 = coeffs.get('s_s2', coeffs.get('s_r2'))

        if s1 is None or s2 is None:
            # This function is specific to strike-slip and reverse.
            # Normal faulting uses 'sigma' directly in _calc_normal.
            raise KeyError(
                "Required coefficients for std_within (s_s1/s_r1 or s_s2/s_r2) not found for strike-slip/reverse style."
            )

        alpha = float(coeffs['alpha'])
        beta = float(coeffs['beta'])
        denom_ab = alpha + beta
        term_shape_center = (alpha / denom_ab) if denom_ab != 0.0 else 0.0

        x = np.atleast_1d(X_L_ratio).astype(float)
        val = s1 + s2 * (x - term_shape_center) ** 2
        return val