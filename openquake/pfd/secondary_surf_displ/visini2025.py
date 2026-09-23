# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
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
Module :mod:`openquake.pfd.secondary_surf_displ.visini2025` implements
the distributed (secondary) fault displacement model of Visini et al. (2025)
in :class:`Visini2025SecondaryFD`.

References
----------
Visini, F., Boncio, P., Valentini, A., Scotti, O., Nurminen, F., Baize, S.,
& Pace, B. (2025). Empirical regressions for distributed faulting of dip-slip
earthquakes. Earthquake Spectra, 41(4), 2968-3001.
https://doi.org/10.1177/87552930241308860
"""
import warnings

import numpy as np
from scipy.stats import norm
from openquake.pfd.params import check_choice, check_style
from openquake.pfd.primary_surf_displ.base import BaseSecondarySurfDispl
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.scalerel.thingbaijam2017 import Thingbaijam2017
from openquake.hazardlib.scalerel.leonard2010 import Leonard2010


# Map of scaling relation names used by this module.  The relations live in
# hazardlib (PR-2 of the oq-engine integration plan); the canonical oq-pfdha
# name "WC1994" is mapped onto the hazardlib :class:`WC1994` class.
_SCALERS = {
    "WC1994": WC1994(),
    "THINGBAIJAM2017": Thingbaijam2017(),
    "LEONARD2010": Leonard2010(),
}


class Visini2025SecondaryFD(BaseSecondarySurfDispl):
    """
    Distributed (secondary) displacement exceedance model (Visini et al., 2025).

    This implements the empirical regression for the exceedance probability
    P(Y > d), assuming a lognormal residual on ln(Y). The regression median
    uses predictors ln(s), ln(TPFm), Mw, style, footwall/hanging-wall, and
    combination offset (A/B/C).

    Parameters used across methods
    ------------------------------
    - d (m):       Displacement threshold.
    - mag (Mw):    Earthquake magnitude.
    - s (m):       Distance to the principal fault trace.
    - rx (m):      Signed cross-fault distance (negative on the footwall).
    - X_L_ratio:   Normalized along-strike position (0..1).
    - dip (deg):   Fault dip angle (affects throw = slip * sin(dip)).
    - tpfm (m):    Mean throw on principal fault. If None, computed from scaling.
    - style:       'normal' or 'reverse'.
    - combination: 'A', 'B', or 'C'.
    - scaling_model: 'WC1994' | 'THINGBAIJAM2017' | 'LEONARD2010'
    - n_sigma: half-width of ln(Y) truncation in σ units (MATLAB scripts use 3).

    Model contract: DISPLACEMENT_DEFINITION = "distributed",
    DISPLACEMENT_COMPONENT = "vertical" -- the predicted quantity Y is the
    vertical throw of Rank 2 distributed ruptures (Visini et al. 2025;
    the regression's TPFm predictor is likewise a throw). Declared
    applicability (in the model's own segments-r metric, see
    MULTIFAULT_REFERENCE_LINE): the paper excludes data closer than 5 m to
    the principal rupture (Visini et al. 2025, pp. 11, 20 -- such
    near-trace scarps are not distinguishable from principal faulting), so
    r_min = 5 m; the outer edges are 10 km on the hanging wall and 8 km on
    the footwall, the dataset range summarised in Valentini et al. (2025,
    Rev. Geophys., Table 4). The paper further differentiates its
    recommended ranges per Combination A/B/C (Visini et al. 2025, p. 14 and
    Conclusion; e.g. Combination B is only meaningful within ~1 km of a
    declared Rank 1.5 trace, cf. the user-manual model page); the values
    declared here are the outermost HW/FW envelope, which is what the
    once-per-run extrapolation warning needs.
    """

    DISPLACEMENT_DEFINITION = "distributed"
    DISPLACEMENT_COMPONENT = "vertical"

    APPLICABILITY_RANGE = {
        "r_min_km": 0.005,
        "r_max_hw_km": 10.0,
        "r_max_fw_km": 8.0,
        "source": "Visini et al. (2025) pp. 11, 20 (5 m exclusion); "
                  "Valentini et al. (2025) Rev. Geophys. Table 4 "
                  "(HW 10 km / FW 8 km dataset envelope)",
    }

    # The Visini regressions are calibrated on distances to the ACTUAL
    # segmented principal rupture, so on multi-fault ruptures s must be the
    # distance to the nearest surface-reaching section (gaps not bridged) -
    # no smoothed ECS/LCP reference line applies.
    MULTIFAULT_REFERENCE_LINE = "segments"

    # Route the distributed contribution through VisiniSecondaryCalculator
    # (combined A/B/C combination + rank-2 Monte Carlo), not the generic
    # P(SR) x P(FD) adapter path (see BaseSecondarySurfDispl.SECONDARY_PIPELINE).
    SECONDARY_PIPELINE = "visini"

    def __init__(self, n_sigma: float = 3.0, truncation_eps: float = None,
                 style=None, scaling_model=None, tpfm=None, case=None,
                 rupture_traces=None) -> None:
        """
        :param n_sigma: half-width of the ln(Y) truncation in sigma units
            (``truncation_eps`` is the deprecated alias).
        :param style: optional coefficient-set selector pinned by the
            logic-tree branch ('normal' or 'reverse'); ``None`` defers to
            the ``get_prob`` call.
        :param scaling_model: optional magnitude-scaling relation for the
            TPFm computation ('WC1994', 'THINGBAIJAM2017' or 'LEONARD2010');
            ``None`` defers to the call (legacy default: 'WC1994').
        :param tpfm: optional fixed total-principal-fault-length measure in
            meters pinned by the logic-tree branch; ``None`` = computed.
        :param case: optional Visini case label (e.g. 'case1'..'case3'),
            consumed by the secondary calculation pipeline; stored as given.
        :param rupture_traces: optional list of rank-1.5 trace names used by
            combination B, consumed by the secondary calculation pipeline;
            stored as given.
        """
        # ``truncation_eps`` is the deprecated former name for ``n_sigma``; it is
        # still accepted (e.g. from older logic-tree configs) and takes priority.
        self.n_sigma = float(truncation_eps if truncation_eps is not None else n_sigma)
        if self.n_sigma <= 0.0:
            raise ValueError(f"n_sigma must be positive; got {self.n_sigma}")
        self.style = check_style(type(self).__name__, style,
                                 frozenset(["normal", "reverse"]))
        self.scaling_model = check_choice(
            type(self).__name__, "scaling_model", scaling_model,
            frozenset(["WC1994", "THINGBAIJAM2017", "LEONARD2010"]),
            canon=lambda v: str(v).upper())
        self.tpfm = None if tpfm is None else float(tpfm)
        self.case = None if case is None else str(case)
        self.rupture_traces = rupture_traces
        # Empirical regression coefficients (ln Y)
        self.coeffs = {
            "a": -8.0651,          # intercept
            "b": -0.2126,          # ln(s) coefficient (s in meters)
            "c": 0.1518,           # ln(TPFm) coefficient
            "d": 1.1426,           # magnitude coefficient
            "e": -0.5259,          # style indicator (normal=1, reverse=0)
            "f": -0.0131,          # footwall indicator (footwall=1, hanging=0)
            "g": {                 # combination offsets
                "A": 0.0,
                "B": 0.0589,
                "C": 1.1193,
            },
            "sigma": 1.0271,       # std. dev. on ln(Y)
        }

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def get_prob(
        self,
        d,
        mag,
        s,
        rx,
        X_L_ratio=0.5,
        dip=90.0,
        tpfm=None,
        style=None,
        combination="A",
        scaling_model=None,
        **kwargs,
    ):
        """
        Return the probability P(Y > d) for secondary displacement exceedance.

        Notes on units:
        - `s` and `rx` are **meters**.
        - `tpfm` is **meters** if provided. If None, it will be computed.

        Optional ``n_sigma`` in ``kwargs`` overrides the instance default
        (e.g. from logic-tree / INI parameters). The legacy name
        ``truncation_eps`` is also accepted.
        """
        n_sigma_override = kwargs.pop("n_sigma", kwargs.pop("truncation_eps", None))
        # Fall back to constructor-pinned values, then legacy defaults
        if style is None:
            style = self.style if self.style is not None else "normal"
        if scaling_model is None:
            scaling_model = (self.scaling_model
                             if self.scaling_model is not None else "WC1994")
        if tpfm is None:
            tpfm = self.tpfm
        # Sanitize inputs
        d = np.asarray(d, dtype=float)
        s = np.asarray(s, dtype=float)
        rx = np.asarray(rx, dtype=float)

        # Compute (or verify) TPFm [m]
        if tpfm is None:
            # Per-site TPFm: compute using a km-based search window equal to each site's s_km
            s_km = s / 1000.0
            # Broadcast X_L_ratio and dip to s's shape
            xlr_b = np.broadcast_to(np.asarray(X_L_ratio, dtype=float), s.shape)
            dip_b = np.broadcast_to(np.asarray(dip, dtype=float), s.shape)

            # DIAGNOSTIC: Check for invalid X_L_ratio values
            xlr_min, xlr_max = float(np.min(xlr_b)), float(np.max(xlr_b))
            if xlr_min < 0.0 or xlr_max > 1.0:
                n_invalid = int(np.sum((xlr_b < 0.0) | (xlr_b > 1.0)))
                warnings.warn(
                    f"Visini2025SecondaryFD.get_prob: X_L_ratio has {n_invalid} values outside [0, 1]. "
                    f"Range: [{xlr_min:.6f}, {xlr_max:.6f}]. "
                    f"This indicates upstream calculation error in rupture_distance.py. "
                    f"Clamping to [0, 1] to prevent NaN.",
                    RuntimeWarning
                )
                xlr_b = np.clip(xlr_b, 0.0, 1.0)

            flat_skm = s_km.reshape(-1)
            flat_xlr = xlr_b.reshape(-1)
            flat_dip = dip_b.reshape(-1)
            flat_tpfm = np.empty_like(flat_skm, dtype=float)

            for i in range(flat_skm.size):
                tpfm_i, _ = self.compute_tpfm_from_scaling(
                    mag,
                    style=style,
                    model=scaling_model,
                    norm_pos=float(flat_xlr[i]),
                    distance=float(flat_skm[i]),  # <-- km per site
                    dip=float(flat_dip[i]),
                )
                flat_tpfm[i] = tpfm_i

            tpfm = flat_tpfm.reshape(s.shape)
        else:
            tpfm = np.asarray(tpfm, dtype=float)

        # Compute regression median and exceedance probability
        median_y = self.get_median_displacement(
            mag=mag, s=s, rx=rx, tpfm=tpfm, style=style, combination=combination
        )

        # Ensure arrays for vectorized sf; guard against non-positive thresholds
        d = np.maximum(d, 1e-16)
        ln_d = np.log(d)
        ln_med = np.log(np.maximum(median_y, 1e-16))
        sigma = float(self.coeffs["sigma"])
        eps = float(
            self.n_sigma
            if n_sigma_override is None
            else n_sigma_override
        )
        if eps <= 0.0:
            raise ValueError(f"n_sigma must be positive; got {eps}")
        denom = norm.cdf(eps) - norm.cdf(-eps)

        # Broadcast to (n_sites, n_displ): displacement thresholds along
        # columns, per-site medians along rows. The orientation must NEVER be
        # inferred from shape equality - when n_sites happens to equal
        # n_displ that heuristic silently produced the element-wise diagonal
        # (site i paired with threshold i) instead of the full matrix.
        ln_d_arr = np.asarray(ln_d)
        ln_med_arr = np.asarray(ln_med)

        if (ln_d_arr.ndim == 1) and (ln_med_arr.ndim == 1):
            ln_d_b = ln_d_arr.reshape((1, -1))
            ln_med_b = ln_med_arr.reshape((-1, 1))
        else:
            ln_d_b = ln_d_arr
            ln_med_b = ln_med_arr

        # P(Y > d) under truncated Normal(ln_med, sigma) with bounds [ln_med - eps*sigma, ln_med + eps*sigma]
        z = (ln_d_b - ln_med_b) / sigma
        p_exceed = (norm.cdf(eps) - norm.cdf(z)) / denom

        # Hard bounds from truncation
        p_exceed = np.where(z <= -eps, 1.0, p_exceed)
        p_exceed = np.where(z >= eps, 0.0, p_exceed)
        p_exceed = np.clip(p_exceed, 0.0, 1.0)

        # Return scalar if scalar input
        if np.asarray(p_exceed).shape == ():
            return float(p_exceed)
        return p_exceed

    def get_median_displacement(self, mag, s, rx, tpfm, style, combination):
        """
        Return the regression median displacement (meters).
        """
        style_l = str(style).lower()
        if style_l not in ("normal", "reverse"):
            raise ValueError(f"style must be 'normal' or 'reverse'; got '{style}'")
        if combination not in ("A", "B", "C"):
            raise ValueError(f"combination must be 'A', 'B', or 'C'; got '{combination}'")

        # Indicators
        sof_indicator = 1 if style_l == "normal" else 0
        rx_arr = np.atleast_1d(rx)
        fw_indicator = np.where(rx_arr < 0.0, 1, 0)  # 1=footwall, 0=hanging wall

        # Coefficients
        p = self.coeffs

        # Prepare predictors (ensure arrays)
        distance = np.maximum(np.atleast_1d(s).astype(float), 1e-8)      # m
        tpfm = np.maximum(np.atleast_1d(tpfm).astype(float), 1e-16)      # m

        ln_s = np.log(distance)
        ln_tpfm = np.log(tpfm)
        g_offset = float(p["g"][combination])

        # Broadcast everything to a common shape
        ln_s, ln_tpfm, rx_arr = np.broadcast_arrays(ln_s, ln_tpfm, rx_arr)
        sof_b = np.broadcast_to(sof_indicator, ln_s.shape)
        fw_b = np.broadcast_to(fw_indicator, ln_s.shape)

        # Equation: ln(Y_med) = a + b*ln(s) + c*ln(TPFm) + d*Mw + e*I_style + f*I_fw + g_comb
        ln_y_med = (
            p["a"]
            + p["b"] * ln_s
            + p["c"] * ln_tpfm
            + p["d"] * float(mag)
            + p["e"] * sof_b
            + p["f"] * fw_b
            + g_offset
        )

        median = np.exp(ln_y_med)
        if median.shape == ():
            return float(median)
        return median

    # --------------------------------------------------------------------- #
    # TPFm construction (scaling + along-strike smoothing)
    # --------------------------------------------------------------------- #
    def compute_tpfm_from_scaling(
        self,
        mag,
        style="normal",
        model="WC1994",
        norm_pos=0.5,
        distance=0.0,
        dip=90.0,
    ):
        """
        Compute mean throw on the principal fault (TPFm) from a magnitude-scaling law,
        then smooth along strike using a window whose half-width increases with
        the site's distance to the PF.

        Parameters
        ----------
        mag : float
            Earthquake moment magnitude (Mw).
        style : str
            'normal' or 'reverse'.
        model : str
            'WC1994' | 'THINGBAIJAM2017' | 'LEONARD2010'
        norm_pos : float
            Normalized along-strike position in [0, 1].
        distance : float
            Site-to-PF distance in **km** (used only to define the smoothing window).
        dip : float
            Fault dip in degrees.

        Returns
        -------
        (tpfm_m, sigma_log10) : (float, float)
            TPFm in meters and the log10 sigma of the average-slip scaling.
        """
        model_u = str(model).upper()
        if model_u not in _SCALERS:
            raise ValueError(f"Unknown scaling model '{model}'")
        sr = _SCALERS[model_u]

        # Average slip AD and its log10 sigma
        ad_m, sigma_log10 = sr.get_average_displacement(mag, style, return_sigma=True)

        # Maximum slip MD (if not available, use 2*AD as a proxy)
        if hasattr(sr, "get_maximum_displacement"):
            md_m = sr.get_maximum_displacement(mag, style)
        else:
            md_m = 2.0 * ad_m

        # Fault length L [km] for computing the along-strike search window
        if hasattr(sr, "get_length_km"):
            L_km = sr.get_length_km(mag, style)
        elif hasattr(sr, "get_median_length"):
            rake = 90.0 if str(style).lower() == "reverse" else -90.0
            L_km = sr.get_median_length(mag, rake)
        elif hasattr(sr, "get_rupture_length"):
            L_km = sr.get_rupture_length(mag)
        elif hasattr(sr, "get_surface_rupture_length"):
            # WC1994 exposes SRL(M) under this name; without this probe the
            # DEFAULT scaling model would silently never activate the
            # distance-dependent along-strike smoothing window (L_km = None
            # forces r = 0 below).
            L_km = sr.get_surface_rupture_length(mag, str(style).lower())
        else:
            L_km = None

        # Half-window r in normalized along-strike coordinate (clip to 0.5)
        if L_km and distance > 0.0:
            r = 0.5 * float(distance) / float(L_km)
            r = min(r, 0.5)
            # DIAGNOSTIC: Check for NaN r (could happen if L_km is NaN)
            if np.isnan(r):
                warnings.warn(
                    f"Visini2025SecondaryFD: r is NaN! L_km={L_km}, distance={distance}. "
                    f"Check scaling relation {model} for this magnitude.",
                    RuntimeWarning
                )
                r = 0.0
        else:
            r = 0.0

        # Construct mean slip (triangular + tapered) and convert to throw by sin(dip)
        x = np.linspace(0.0, 1.0, 1001)
        tri_shape = np.maximum(1.0 - 2.0 * np.abs(x - 0.5), 0.0)          # triangular
        tap_shape = np.sqrt(np.sin(np.pi * x))                             # tapered
        D_tri = md_m * tri_shape
        D_tap = 1.311 * ad_m * tap_shape
        D_mean = 0.5 * (D_tri + D_tap)
        T_mean = D_mean * np.sin(np.radians(dip))

        # Sample or smooth around norm_pos
        # DIAGNOSTIC: Check for invalid norm_pos values and warn (not silently clamp)
        if norm_pos < 0.0 or norm_pos > 1.0:
            warnings.warn(
                f"Visini2025SecondaryFD: norm_pos={norm_pos:.6f} is outside [0, 1]. "
                f"This indicates upstream X_L_ratio computation is incorrect. "
                f"Check rupture_distance.py calculate_x_l_ratios(). "
                f"Parameters: mag={mag}, style={style}, distance_km={distance:.4f}, r={r:.6f}. "
                f"Clamping to [0, 1] to prevent NaN.",
                RuntimeWarning
            )
            norm_pos = max(0.0, min(1.0, norm_pos))

        if r == 0.0:
            tpfm_loc = float(np.interp(norm_pos, x, T_mean))
        else:
            left = max(0.0, norm_pos - r)
            right = min(1.0, norm_pos + r)
            mask = (x >= left) & (x <= right)
            # Safety: if mask is empty (should not happen after clamping), fallback to interpolation
            if not np.any(mask):
                tpfm_loc = float(np.interp(norm_pos, x, T_mean))
            else:
                tpfm_loc = float(np.mean(T_mean[mask]))

        return tpfm_loc, float(sigma_log10)