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
Module :mod:`openquake.pfd.secondary_surf_rup.visini2025` implements the
distributed (secondary) rupture occurrence model of Visini et al. (2025) in
:class:`Visini2025SecondarySR`.

Supported fault styles: normal and reverse (dip-slip).

References
----------
Visini, F., Boncio, P., Valentini, A., Scotti, O., Nurminen, F., Baize, S.,
& Pace, B. (2025). Empirical regressions for distributed faulting of dip-slip
earthquakes. Earthquake Spectra, 41(4), 2968-3001.
https://doi.org/10.1177/87552930241308860

Implementation notes
--------------------
The across-strike occurrence probability uses the logistic regressions of
Table 2; the along-strike participation uses the F-ratio lookups of Table 3
combined with a Monte Carlo sampling of distributed-rupture segment lengths
(truncated lognormal). Monte Carlo results are cached per
``(fault_length, mechanism, hw_fw, near_far, site_width)`` because the
along-strike probability depends only on those geometric parameters, and the
per-site evaluation is vectorized.
"""

import zlib
from bisect import bisect_right

import numpy as np
from scipy.stats import lognorm

from openquake.pfd.params import check_choice, check_positive, check_style
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup


class Visini2025SecondarySR(BaseSecondarySurfRup):
    """
    Distributed (secondary) rupture occurrence model of Visini et al. (2025)
    for normal- and reverse-faulting earthquakes, as a function of magnitude,
    distance from the principal trace, hanging-wall/footwall position, and
    analysis cell (slice) width.

    References
    ----------
    Visini, F., Boncio, P., Valentini, A., Scotti, O., Nurminen, F., Baize,
    S., & Pace, B. (2025). Empirical regressions for distributed faulting of
    dip-slip earthquakes. Earthquake Spectra, 41(4), 2968-3001.
    https://doi.org/10.1177/87552930241308860
    """

    # The Visini regressions are calibrated on distances to the ACTUAL
    # segmented principal rupture, so on multi-fault ruptures r must be the
    # distance to the nearest surface-reaching section (gaps not bridged) -
    # no smoothed ECS/LCP reference line applies.
    MULTIFAULT_REFERENCE_LINE = "segments"

    # Route the distributed contribution through VisiniSecondaryCalculator
    # (combined A/B/C combination + rank-2 Monte Carlo), not the generic
    # P(SR) x P(FD) adapter path (see BaseSecondarySurfRup.SECONDARY_PIPELINE).
    SECONDARY_PIPELINE = "visini"

    def __init__(self, style=None, pixel_size=None, segment_sampling=None,
                 rupture_traces=None, along_strike_width=None,
                 distribution_type=None):
        """
        :param style: optional coefficient-set selector pinned by the
            logic-tree branch ('normal' or 'reverse'); ``None`` defers to
            the ``get_prob`` call.
        :param pixel_size: optional across-strike cell size in meters pinned
            by the logic-tree branch; ``None`` defers to the call.
        :param segment_sampling: optional Rank-2 along-strike sampling
            variant (e.g. 'truncated', 'legacy'), consumed by the secondary
            (Visini) calculation pipeline; stored as given.
        :param rupture_traces: optional list of rank-1.5 trace names used by
            combination B, consumed by the secondary calculation pipeline;
            stored as given.
        :param along_strike_width: optional along-strike site-cell width in
            meters (defaults to ``pixel_size`` downstream), consumed by the
            secondary calculation pipeline.
        :param distribution_type: optional Rank-2 placement algorithm
            ('uniform', 'exponential' or 'average'), consumed by the
            secondary calculation pipeline.
        """
        super().__init__()
        self.style = check_style(type(self).__name__, style,
                                 frozenset(["normal", "reverse"]))
        self.pixel_size = check_positive(type(self).__name__, "pixel_size",
                                         pixel_size)
        self.segment_sampling = (None if segment_sampling is None
                                 else str(segment_sampling))
        self.rupture_traces = rupture_traces
        self.along_strike_width = check_positive(
            type(self).__name__, "along_strike_width", along_strike_width)
        self.distribution_type = check_choice(
            type(self).__name__, "distribution_type", distribution_type,
            ("uniform", "exponential", "average"))

        # Logistic regression coefficients from Table 2 (unchanged)
        self.coeffs_occurrence = {
            'normal': {
                10: {'A': {'a': 5.903214, 'b': -0.950792, 'c': 0.000891, 'd': 1.373730},
                     'B': {'a': 3.942908, 'b': -0.472749, 'c': 0.002441, 'd': 0.070138},
                     'C': {'a': 5.992004, 'b': -0.828323, 'c': 0.000185, 'd': 0.869644}},
                20: {'A': {'a': 5.898758, 'b': -0.950792, 'c': 0.000891, 'd': 1.373730},
                     'B': {'a': 3.930705, 'b': -0.472749, 'c': 0.002441, 'd': 0.070138},
                     'C': {'a': 5.991077, 'b': -0.828323, 'c': 0.000185, 'd': 0.869644}},
                50: {'A': {'a': 5.885388, 'b': -0.950792, 'c': 0.000891, 'd': 1.373730},
                     'B': {'a': 3.895606, 'b': -0.472668, 'c': 0.002435, 'd': 0.070126},
                     'C': {'a': 5.988296, 'b': -0.828323, 'c': 0.000185, 'd': 0.869644}},
                100:{'A': {'a': 5.863104, 'b': -0.950792, 'c': 0.000891, 'd': 1.373730},
                     'B': {'a': 3.836451, 'b': -0.472584, 'c': 0.002430, 'd': 0.070114},
                     'C': {'a': 5.983659, 'b': -0.828323, 'c': 0.000185, 'd': 0.869644}},
                200:{'A': {'a': 5.818538, 'b': -0.950792, 'c': 0.000891, 'd': 1.373730},
                     'B': {'a': 3.720450, 'b': -0.472362, 'c': 0.002415, 'd': 0.070081},
                     'C': {'a': 5.974377, 'b': -0.828323, 'c': 0.000185, 'd': 0.869644}},
                500:{'A': {'a': 5.684838, 'b': -0.950792, 'c': 0.000891, 'd': 1.373730},
                     'B': {'a': 3.388553, 'b': -0.471574, 'c': 0.002355, 'd': 0.069965},
                     'C': {'a': 5.946468, 'b': -0.828323, 'c': 0.000185, 'd': 0.869644}},
            },
            'reverse': {
                10: {'A': {'a': 9.247414, 'b': -1.318981, 'c': 0.000782, 'd': 1.102631},
                     'B': {'a': 24.976166, 'b': -3.292095, 'c': 0.003027, 'd': 2.441285},
                     'C': {'a': 18.650294, 'b': -2.516707, 'c': 0.000398, 'd': 2.360062}},
                20: {'A': {'a': 9.243505, 'b': -1.318981, 'c': 0.000782, 'd': 1.102631},
                     'B': {'a': 24.961029, 'b': -3.292095, 'c': 0.003027, 'd': 2.441285},
                     'C': {'a': 18.648305, 'b': -2.516707, 'c': 0.000398, 'd': 2.360062}},
                50: {'A': {'a': 9.231778, 'b': -1.318981, 'c': 0.000782, 'd': 1.102631},
                     'B': {'a': 24.914213, 'b': -3.291712, 'c': 0.003024, 'd': 2.440953},
                     'C': {'a': 18.642338, 'b': -2.516707, 'c': 0.000398, 'd': 2.360062}},
                100:{'A': {'a': 9.212234, 'b': -1.318981, 'c': 0.000782, 'd': 1.102631},
                     'B': {'a': 24.837260, 'b': -3.291312, 'c': 0.003020, 'd': 2.440606},
                     'C': {'a': 18.632394, 'b': -2.516707, 'c': 0.000398, 'd': 2.360063}},
                200:{'A': {'a': 9.173145, 'b': -1.318981, 'c': 0.000782, 'd': 1.102631},
                     'B': {'a': 24.683195, 'b': -3.290227, 'c': 0.003009, 'd': 2.439663},
                     'C': {'a': 18.612507, 'b': -2.516709, 'c': 0.000398, 'd': 2.360064}},
                500:{'A': {'a': 9.055878, 'b': -1.318981, 'c': 0.000782, 'd': 1.102631},
                     'B': {'a': 24.227872, 'b': -3.286136, 'c': 0.002965, 'd': 2.436083},
                     'C': {'a': 18.552863, 'b': -2.516718, 'c': 0.000398, 'd': 2.360074}},
            }
        }

        # F-ratio lookup (97.5th percentile) from Table 3
        self._f_ratio = {
            "normal": {
                "HW": {
                    "near": {10:0.02052,20:0.03171,50:0.05298,100:0.07413,200:0.09771,500:0.13565},
                    "far":  {10:0.00201,20:0.00398,50:0.01035,100:0.02005,200:0.03689,500:0.04013}
                },
                "FW": {
                    "near": {10:0.00800,20:0.01197,50:0.02148,100:0.02941,200:0.03619,500:0.05050},
                    "far":  {10:0.00082,20:0.00153,50:0.00388,100:0.00797,200:0.01539,500:0.01712}
                }
            },
            "reverse": {
                "HW": {
                    "near": {10:0.03105,20:0.04809,50:0.08194,100:0.11202,200:0.13873,500:0.18748},
                    "far":  {10:0.00208,20:0.00390,50:0.01041,100:0.02128,200:0.03806,500:0.02006}
                },
                "FW": {
                    "near": {10:0.01179,20:0.01773,50:0.02452,100:0.03102,200:0.03999,500:0.04453},
                    "far":  {10:0.00020,20:0.00037,50:0.00098,100:0.00215,200:0.00360,500:0.00138}
                }
            }
        }

        # Lognormal parameters (precomputed)
        self._logn_params = {
            "reverse": {"HW": (3.622, 1.589), "FW": (3.801, 1.542)},
            "normal": {"HW": (3.546, 1.358), "FW": (3.390, 1.472)}
        }

        # DR length min/max bounds
        self._drlengths_min_max = {
            "reverse": {"HW": (8.0, 248.0), "FW": (10.0, 249.0)},
            "normal":  {"HW": (8.0, 137.0), "FW": (6.0, 131.0)}
        }

        # Width bins for F-ratio lookup
        self._width_bins = [10, 20, 50, 100, 200, 500]

        # Monte Carlo cache: key -> P_along_strike value
        # This is the critical optimization - we cache MC results
        self._mc_cache = {}

        # Precompute PDF tables for each (mechanism, hw_fw) pair
        self._pdf_tables = {}
        self._draw_tables = {}
        self._precompute_pdf_tables()

    def _precompute_pdf_tables(self):
        """Precompute truncated lognormal PDF tables for fast sampling."""
        for mechanism in ["normal", "reverse"]:
            for hw_fw in ["HW", "FW"]:
                logn_mu, logn_sigma = self._logn_params[mechanism][hw_fw]
                t1, t2 = self._drlengths_min_max[mechanism][hw_fw]
                t1i, t2i = int(t1), int(t2)

                x = np.arange(t1i, t2i + 1, dtype=float)
                pdf = lognorm(s=logn_sigma, scale=np.exp(logn_mu)).pdf(x)
                pdf = pdf / np.sum(pdf)

                self._pdf_tables[(mechanism, hw_fw)] = (x, pdf, t1i, t2i)
                # Fast-draw table: numpy Generator.choice(x, p=pdf) draws ONE
                # uniform and inverts the CDF built as cumsum(p)/cumsum(p)[-1]
                # with searchsorted(side='right'). Precomputing that exact CDF
                # once (choice rebuilds it - and re-validates dtypes - on
                # EVERY draw) and inverting with bisect keeps the random
                # stream bit-identical while removing ~90% of the MC cost.
                cdf = pdf.cumsum()
                cdf = cdf / cdf[-1]
                self._draw_tables[(mechanism, hw_fw)] = (
                    x.tolist(), cdf.tolist(), len(x) - 1)

    def get_prob(self, mag, r, rx, style=None, pixel_size=None,
                 combination="A"):
        """
        Required method for BaseSecondarySurfRup.

        OPTIMIZED: Accepts both scalar and array inputs for r and rx.
        """
        # Fall back to constructor-pinned values (call argument wins)
        if style is None:
            style = self.style
        if pixel_size is None:
            pixel_size = self.pixel_size
        if style is None or pixel_size is None:
            raise ValueError(
                f"{type(self).__name__}: style and pixel_size must be given "
                f"either in the logic-tree branch or at call time")
        return self.get_prob_slice(mag, r, rx, style, pixel_size, combination)

    def get_prob_slice(self, mag, r, rx, style, pixel_size, combination):
        """
        Calculate logistic regression probability P_slice.

        OPTIMIZED: Fully vectorized over all sites.

        Parameters:
        -----------
        mag : float
            Moment magnitude
        r : float or array
            Minimum distance from the slice to PF (m)
        rx : float or array
            Horizontal distance to surface projection of fault (negative for footwall)
        style : str
            'normal' or 'reverse'
        pixel_size : int
            Width of the slice (m)
        combination : str
            'A', 'B', or 'C'

        Returns:
        --------
        float or array
            P_slice probability for each input site
        """
        if style not in self.coeffs_occurrence:
            raise ValueError("style must be 'normal' or 'reverse'")
        if pixel_size not in self.coeffs_occurrence[style]:
            raise ValueError("pixel_size must be one of {list(self.coeffs_occurrence[style].keys())}")
        if combination not in ('A','B','C'):
            raise ValueError("combination must be 'A','B' or 'C'")

        # Get coefficients (single lookup)
        coeffs = self.coeffs_occurrence[style][pixel_size][combination]
        a, b, c, d = coeffs['a'], coeffs['b'], coeffs['c'], coeffs['d']

        # Convert to arrays for vectorized computation
        r_arr = np.atleast_1d(np.asarray(r, dtype=float))
        rx_arr = np.atleast_1d(np.asarray(rx, dtype=float))

        # Ensure same shape via broadcasting
        r_arr, rx_arr = np.broadcast_arrays(r_arr, rx_arr)

        # FW indicator: 1 for footwall (rx < 0), 0 for hanging wall
        # VECTORIZED over all sites
        fw = np.where(rx_arr < 0, 1, 0)

        # Equation 2 from paper: linear predictor (VECTORIZED)
        y = a + b * mag + c * r_arr + d * fw

        # Equation 1 from paper: logistic function
        # Using numerically stable form: 1/(1+exp(y)) = sigmoid(-y)
        # p = 1 - exp(y)/(1+exp(y)) = 1/(1+exp(y))
        exp_y = np.exp(y)
        p = 1.0 - exp_y / (1.0 + exp_y)

        # Return scalar if input was scalar
        if p.size == 1:
            return float(p[0])
        return p

    def get_prob_slice_vectorized(self, mag, r, rx, style, pixel_size, combination):
        """
        Alias for vectorized P_slice computation.
        Same as get_prob_slice but explicitly named for clarity.
        """
        return self.get_prob_slice(mag, r, rx, style, pixel_size, combination)

    def _get_mc_cache_key(self, fault_length, across_strike_width, along_strike_width,
                          hanging_wall_or_footwall, mechanism, near_or_far,
                          distribution_type="uniform"):
        """
        Generate cache key for Monte Carlo results.

        MATHEMATICAL JUSTIFICATION:
        P_along_strike depends ONLY on these parameters because:
        1. fault_length determines total DR length = fault_length × F_ratio
        2. across_strike_width determines F_ratio lookup (Table 3)
        3. along_strike_width determines Monte Carlo site window
        4. mechanism determines lognormal parameters and F_ratio
        5. HW/FW determines lognormal parameters and F_ratio
        6. near/far determines F_ratio
        7. distribution_type determines which placement algorithm is used

        The site is always placed at fault center (standardized), so individual
        site distances do NOT affect P_along_strike.

        We discretize fault_length to 100m bins and along_strike_width to 10m bins
        to limit cache size while maintaining accuracy.
        """
        # Round fault_length to nearest 100m for cache key
        fl_rounded = int(round(fault_length / 100.0) * 100)
        # Round along_strike_width to nearest 10m for cache efficiency
        along_rounded = int(round(along_strike_width / 10.0) * 10)
        return (fl_rounded, across_strike_width, along_rounded, hanging_wall_or_footwall,
                mechanism, near_or_far, distribution_type)

    def monte_carlo_rank2_occurrence(self, fault_length, across_strike_width,
                                    hanging_wall_or_footwall, mechanism, near_or_far,
                                    num_simulations=10000, use_cache=True,
                                    distribution_type="uniform",
                                    segment_sampling="truncated",
                                    along_strike_width=None):
        """
        Monte Carlo simulation to compute P_along_strike.

        OPTIMIZED: Results are cached by (fault_length, across_strike_width,
        along_strike_width, mechanism, hw_fw, near_far, distribution_type, segment_sampling).

        Parameters:
        -----------
        fault_length : float
            Total fault length in meters
        across_strike_width : int
            Site width perpendicular to PF (m).
            Must be one of: 10, 20, 50, 100, 200, 500.
            Used for F-ratio lookup (Table 3).
            (Formerly named 'site_width' - backward compatible)
        hanging_wall_or_footwall : str
            'HW' or 'FW'
        mechanism : str
            'normal' or 'reverse' (will be normalized to lowercase)
        near_or_far : str
            'near' or 'far'
        num_simulations : int
            Number of Monte Carlo simulations (default 10000)
        use_cache : bool
            Whether to use caching (default True)
        distribution_type : str
            "uniform" (default), "exponential", or "average"
            - "uniform": Only run uniform distribution (MATLAB randperm style)
            - "exponential": Only run exponential distribution (clustered)
            - "average": Run both and return (P_uniform + P_exponential) / 2
        segment_sampling : str
            "truncated" (default): Use truncated lognormal with 16th-84th percentile
                        bounds per MATLAB specification
            "legacy": Use raw lognormal clipped to [10, fault_length]
                     for backward compatibility with previous results
        along_strike_width : float, optional
            Site extent parallel to PF (m). Can be any positive value.
            Used only for intersection check in Monte Carlo.
            If None, uses across_strike_width for backward compatibility (square site).

        Returns:
        --------
        float
            P_along_strike probability
        """
        # Backward compatibility: if along_strike_width not provided, use across_strike_width
        if along_strike_width is None:
            along_strike_width = across_strike_width

        mechanism_lower = mechanism.lower()

        # Validate across_strike_width (should be in predefined bins, but find closest)
        closest_across = min(self._width_bins, key=lambda x: abs(x - across_strike_width))
        if across_strike_width not in self._width_bins:
            import warnings
            warnings.warn(
                f"across_strike_width={across_strike_width} not in {self._width_bins}, "
                f"using closest value {closest_across} for F-ratio lookup"
            )

        # Validate along_strike_width (any positive value)
        if along_strike_width <= 0:
            raise ValueError(f"along_strike_width must be positive, got {along_strike_width}")

        # Validate distribution_type
        if distribution_type not in ("uniform", "exponential", "average"):
            raise ValueError(
                f"distribution_type must be 'uniform', 'exponential', or 'average', "
                f"got '{distribution_type}'"
            )

        # Validate segment_sampling
        if segment_sampling not in ("legacy", "truncated"):
            raise ValueError(
                f"segment_sampling must be 'legacy' or 'truncated', "
                f"got '{segment_sampling}'"
            )

        # Check cache first (include segment_sampling in cache key)
        if use_cache:
            cache_key = self._get_mc_cache_key(
                fault_length, closest_across, along_strike_width, hanging_wall_or_footwall,
                mechanism_lower, near_or_far, distribution_type
            ) + (segment_sampling,)
            if cache_key in self._mc_cache:
                return self._mc_cache[cache_key]

        # F-ratio lookup uses ACROSS-STRIKE width (must be in predefined bins)
        F = self._f_ratio[mechanism_lower][hanging_wall_or_footwall][near_or_far][closest_across]
        total_DR_length = fault_length * F

        # Monte Carlo site window uses ALONG-STRIKE width (can be any value)
        L = int(fault_length)
        site_lo = int(fault_length / 2 - along_strike_width / 2)
        site_hi = int(fault_length / 2 + along_strike_width / 2)

        # Get lognormal parameters for segment length sampling
        logn_mu, logn_sigma = self._logn_params[mechanism_lower][hanging_wall_or_footwall]

        # For truncated sampling, get the precomputed fast-draw table
        # (exact CDF that Generator.choice would rebuild on every draw)
        if segment_sampling == "truncated":
            x_list, cdf_list, i_max = self._draw_tables[
                (mechanism_lower, hanging_wall_or_footwall)]

        # Local RNG (no global np.random.seed() pollution), seeded
        # deterministically from the physical inputs: identical parameters
        # must give identical P_along_strike across runs and processes,
        # otherwise hazard curves carry O(1/sqrt(num_simulations)) run-to-run
        # noise (~8% observed at 10000 samples). crc32 rather than hash():
        # Python string hashing is salted per process.
        seed_key = (int(round(fault_length)), closest_across,
                    int(round(along_strike_width)), hanging_wall_or_footwall,
                    mechanism_lower, near_or_far, distribution_type,
                    segment_sampling, int(num_simulations))
        rng = np.random.default_rng(zlib.crc32(repr(seed_key).encode()))

        hits_uniform = 0
        hits_exponential = 0

        run_uniform = distribution_type in ("uniform", "average")
        run_exponential = distribution_type in ("exponential", "average")

        for _ in range(num_simulations):
            # Sample segment lengths based on segment_sampling mode
            segments = []
            total = 0.0
            while total < total_DR_length and len(segments) < 1000:
                if segment_sampling == "truncated":
                    # MATLAB-style: truncated lognormal with 16th-84th
                    # percentile bounds. Bit-identical fast path for
                    # rng.choice(x, p=pdf): same single uniform, same
                    # CDF-inversion index, precomputed table.
                    seg_len = x_list[
                        min(bisect_right(cdf_list, rng.random()), i_max)]
                else:
                    # Legacy: raw lognormal clipped to [10, fault_length]
                    seg_len = float(rng.lognormal(logn_mu, logn_sigma))
                    seg_len = max(seg_len, 10.0)
                    seg_len = min(seg_len, float(fault_length))
                segments.append(seg_len)
                total += seg_len

            if not segments:
                continue

            num_segments = len(segments)

            # ===== UNIFORM DISTRIBUTION (Fix 4: randperm style) =====
            if run_uniform:
                # Fix 4: Use choice(replace=False) + sort + overlap adjustment
                # MATLAB: Centro_Seg_Simulati_unif = randperm(SpaceDRLength, NumSeg);
                if num_segments <= L:
                    positions = rng.choice(L, size=num_segments, replace=False)
                else:
                    # Fallback if more segments than positions
                    positions = rng.integers(0, L, size=num_segments)

                centro_unif = np.sort(positions).astype(float)

                # Compute cumulative semi-lengths for overlap adjustment
                semi_lengths = np.array(segments) / 2.0
                cum_semi = np.cumsum(semi_lengths)

                # Adjust overlapping segments by shifting (MATLAB overlap fix)
                for g in range(1, len(centro_unif)):
                    gap = centro_unif[g] - centro_unif[g - 1]
                    threshold = int(cum_semi[g - 1])
                    if gap < threshold:
                        centro_unif[g] = centro_unif[g] + threshold

                # Check if any segment hits the site
                site_hit_unif = False
                for j, seg_len in enumerate(segments):
                    center = centro_unif[j]
                    semi = seg_len / 2.0
                    start = int(max(0, np.floor(center - semi)))
                    end = int(min(L, np.ceil(center + semi)))
                    # Check overlap with site window
                    if end >= start and end >= site_lo and start <= site_hi:
                        site_hit_unif = True
                        break

                if site_hit_unif:
                    hits_uniform += 1

            # ===== EXPONENTIAL DISTRIBUTION (Fix 2: clustered placement) =====
            if run_exponential:
                # Fix 2: Random starting position + exponential inter-segment gaps
                mean_distance = L / num_segments
                starting_pos = rng.integers(1, L + 1)
                interdistance = rng.exponential(mean_distance, num_segments)

                ini_s = float(starting_pos)
                site_hit_exp = False

                for j in range(num_segments):
                    end_s = ini_s + segments[j]

                    # Wrap-around when position exceeds fault length
                    if ini_s > L or end_s > L:
                        ini_s = ini_s - L
                        end_s = end_s - L

                    start_i = int(np.floor(ini_s))
                    end_i = int(np.ceil(end_s))

                    # Check overlap with site window
                    if end_i >= start_i and end_i >= site_lo and start_i <= site_hi:
                        site_hit_exp = True

                    # Next segment starts after current end + exponential gap
                    ini_s = end_s + int(interdistance[j])

                if site_hit_exp:
                    hits_exponential += 1

        # Compute result based on distribution_type
        if distribution_type == "uniform":
            prob_result = hits_uniform / num_simulations if num_simulations > 0 else 0.0
        elif distribution_type == "exponential":
            prob_result = hits_exponential / num_simulations if num_simulations > 0 else 0.0
        else:  # "average"
            prob_uniform = hits_uniform / num_simulations if num_simulations > 0 else 0.0
            prob_exponential = hits_exponential / num_simulations if num_simulations > 0 else 0.0
            prob_result = 0.5 * (prob_uniform + prob_exponential)

        # Cache the result
        if use_cache:
            self._mc_cache[cache_key] = prob_result

        return prob_result

    def calculate_rank2_total_probability(self, mag, r, rx, style,
                                         across_strike_width, along_strike_width=None,
                                         combination=None, fault_length=None,
                                         near_or_far=None, num_simulations=10000,
                                         distribution_type="uniform",
                                         segment_sampling="truncated"):
        """
        Calculate total probability P(site) = P(across) × P(along).

        OPTIMIZED: P_slice is vectorized, P_along is cached.

        Parameters:
        -----------
        mag : float
            Moment magnitude
        r : float or array
            Distance from site to PF (m)
        rx : float or array
            Signed distance (negative = footwall)
        style : str
            'normal' or 'reverse'
        across_strike_width : int
            Site width perpendicular to PF (m).
            Must be one of: 10, 20, 50, 100, 200, 500.
            Used for P(across) coefficient lookup (Table 2) and F-ratio lookup (Table 3).
        along_strike_width : float, optional
            Site extent parallel to PF (m). Can be any positive value.
            Used only for Monte Carlo intersection check.
            If None, uses across_strike_width for backward compatibility.
        combination : str
            'A', 'B', or 'C'
        fault_length : float
            Total fault length (m)
        near_or_far : str
            'near' or 'far'
        num_simulations : int
            Number of Monte Carlo simulations
        distribution_type : str
            "uniform", "exponential", or "average"
        segment_sampling : str
            "truncated" or "legacy"

        Returns:
        --------
        dict with P_slice (P_across), P_along_strike, P_total
        """
        # Backward compatibility: if along_strike_width not provided, use across_strike_width
        if along_strike_width is None:
            along_strike_width = across_strike_width

        # P(across) uses across_strike_width for coefficient lookup
        P_slice = self.get_prob_slice(mag, r, rx, style, across_strike_width, combination)

        # P(along) uses both dimensions
        hw_or_fw = 'FW' if np.any(np.asarray(rx) < 0) else 'HW'
        mechanism = style.lower()

        P_along = self.monte_carlo_rank2_occurrence(
            fault_length,
            across_strike_width,
            hw_or_fw,
            mechanism,
            near_or_far,
            num_simulations=num_simulations,
            distribution_type=distribution_type,
            segment_sampling=segment_sampling,
            along_strike_width=along_strike_width
        )

        # Total probability
        P_total = P_slice * P_along

        return {
            "P_slice": P_slice,
            "P_along_strike": P_along,
            "P_total": P_total
        }

    def calculate_rank2_total_probability_vectorized(self, mag, r_array, rx_array,
                                                     style, across_strike_width, combination,
                                                     fault_length, along_strike_width=None,
                                                     near_far_array=None, num_simulations=10000,
                                                     distribution_type="uniform",
                                                     segment_sampling="truncated"):
        """
        FULLY VECTORIZED calculation for all sites at once.

        This is the main optimization entry point for hazard map calculations.

        Parameters:
        -----------
        mag : float
            Moment magnitude
        r_array : array
            Distance from each site to PF (m)
        rx_array : array
            Signed distance for each site (m, negative = footwall)
        style : str
            'normal' or 'reverse'
        across_strike_width : int
            Site width perpendicular to PF (m).
            Must be one of: 10, 20, 50, 100, 200, 500.
            Used for P(across) coefficient lookup (Table 2) and F-ratio lookup (Table 3).
        combination : str
            'A', 'B', or 'C'
        fault_length : float
            Total fault length (m)
        along_strike_width : float, optional
            Site extent parallel to PF (m). Can be any positive value.
            Used only for Monte Carlo intersection check.
            If None, uses across_strike_width for backward compatibility.
        near_far_array : array of str
            'near' or 'far' for each site
        num_simulations : int
            MC simulations
        distribution_type : str
            "uniform", "exponential", or "average"
        segment_sampling : str
            "truncated" or "legacy"

        Returns:
        --------
        dict with arrays:
            P_slice: array of per-site slice probabilities
            P_along_strike: array of per-site along-strike probabilities
            P_total: array of per-site total probabilities
        """
        # Backward compatibility: if along_strike_width not provided, use across_strike_width
        if along_strike_width is None:
            along_strike_width = across_strike_width

        r_arr = np.atleast_1d(np.asarray(r_array, dtype=float))
        rx_arr = np.atleast_1d(np.asarray(rx_array, dtype=float))
        near_far_arr = np.atleast_1d(near_far_array)

        n_sites = len(r_arr)
        mechanism = style.lower()

        # Step 1: Compute P_slice for ALL sites at once (vectorized)
        # P(across) uses across_strike_width for coefficient lookup
        P_slice = self.get_prob_slice(mag, r_arr, rx_arr, style, across_strike_width, combination)
        P_slice = np.atleast_1d(P_slice)

        # Step 2: Compute P_along for each unique (hw_fw, near_far) group
        # There are at most 4 groups: (HW,near), (HW,far), (FW,near), (FW,far)
        hw_fw_arr = np.where(rx_arr < 0, 'FW', 'HW')

        # Get unique groups
        P_along = np.zeros(n_sites, dtype=float)

        for hw_fw in ['HW', 'FW']:
            for near_far in ['near', 'far']:
                mask = (hw_fw_arr == hw_fw) & (near_far_arr == near_far)
                if not np.any(mask):
                    continue

                # Single MC call for this group (cached)
                # P(along) uses both dimensions
                p_along_group = self.monte_carlo_rank2_occurrence(
                    fault_length,
                    across_strike_width,
                    hw_fw,
                    mechanism,
                    near_far,
                    num_simulations=num_simulations,
                    distribution_type=distribution_type,
                    segment_sampling=segment_sampling,
                    along_strike_width=along_strike_width
                )
                P_along[mask] = p_along_group

        P_total = P_slice * P_along

        return {
            "P_slice": P_slice,
            "P_along_strike": P_along,
            "P_total": P_total
        }

    def clear_cache(self):
        """Clear the Monte Carlo cache."""
        self._mc_cache.clear()

    def get_cache_stats(self):
        """Return cache statistics for debugging."""
        return {
            "cache_size": len(self._mc_cache),
            "cache_keys": list(self._mc_cache.keys())[:10]  # First 10 keys
        }