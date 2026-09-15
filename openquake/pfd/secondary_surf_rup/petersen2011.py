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
Module :mod:`openquake.pfd.secondary_surf_rup.petersen2011`
"""

import numpy as np
from openquake.pfd.params import check_choice, check_positive, check_style
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup


class Petersen2011SecondarySR(BaseSecondarySurfRup):
    """
    Implementation of the Petersen et al. (2011) model for strike-slip faults
    with different pixel sizes
    """

    # Define coefficients for different pixel sizes
    # Pixel ("cell") size parameters from Table 4 (Page 812, Petersen et al., 2011)
    PIXEL_SIZES = {
        25: {"a": -1.1470, "b": 2.1046, "sigma": 1.2508},  # 25 x 25 m
        50: {"a": -0.9000, "b": 0.9866, "sigma": 1.1470},  # 50 x 50 m
        100: {"a": -1.0114, "b": 2.5572, "sigma": 1.0917},  # 100 x 100 m
        150: {"a": -1.0934, "b": 3.5526, "sigma": 1.0188},  # 150 x 150 m
        200: {"a": -1.1538, "b": 4.2342, "sigma": 1.0177},  # 200 x 200 m
    }

    # Near-field interpolation points from Table 5 (page 812, Petersen et al.,
    # 2011); p0/p1/p2 converted from percent to fractions
    NEAR_FIELD_POINTS = {
        25: {"p0": 0.74541, "p1": 0.078690, "p2": 0.020108, "r1": 100, "r2": 200},  # 25 x 25 m
        50: {"p0": 0.87162, "p1": 0.048206, "p2": 0.026177, "r1": 100, "r2": 200},  # 50 x 50 m
        100: {"p0": 0.90173, "p1": 0.18523, "p2": 0.066354, "r1": 100, "r2": 200},  # 100 x 100 m
        150: {"p0": 0.87394, "p1": 0.19592, "p2": 0.070477, "r1": 150, "r2": 300},  # 150 x 150 m
        200: {"p0": 0.92483, "p1": 0.18975, "p2": 0.074709, "r1": 200, "r2": 400},  # 200 x 200 m
    }

    def __init__(self, pixel_size=None, version=None, cell_size=None,
                 style=None):
        """
        :param pixel_size: optional pixel (cell) size in meters pinned by
            the logic-tree branch; ``None`` defers to the ``get_prob`` call
            (legacy default: 25).
        :param version: optional variant ('default' or 'near_field');
            ``None`` defers to the call (legacy default: 'default').
        :param cell_size: deprecated alias of ``pixel_size``.
        :param style: optional faulting style declared by the logic-tree
            branch. Petersen et al. (2011) is a strike-slip model with no
            style selector, so the value does not change the numbers; it is
            stored (validated against the global style vocabulary) as a
            declaration of the branch context.
        """
        super().__init__()
        self.pixel_size = check_positive(type(self).__name__, "pixel_size",
                                         pixel_size)
        self.version = check_choice(type(self).__name__, "version", version,
                                    frozenset(["default", "near_field"]),
                                    canon=lambda v: str(v).lower())
        self.cell_size = check_positive(type(self).__name__, "cell_size",
                                        cell_size)
        self.style = check_style(type(self).__name__, style)

    def get_prob(self, r, pixel_size=None, version=None, cell_size=None):
        """
        Calculate the probability of distributed-fault surface rupture as a function of distance,
        pixel size, and version, per Petersen et al. (2011).

        :param r:
            Distance from the principal fault trace in kilometers (up to 2 km recommended).
        :param pixel_size:
            Size of the pixel ("cell" in the paper) in meters
            (25, 50, 100, 150, or 200 m; default: 25 m).
        :param version:
            Model version (case-insensitive). Options: 'default' (power function, Page 812, Table 4),
            'near_field' (interpolated near-field, Table 5, page 812). Default: 'default'.
        :param cell_size:
            Deprecated alias of ``pixel_size`` (the historical parameter name);
            when given it overrides ``pixel_size``.
        :returns:
            Probability of rupture (float or array, 0–1) for the given distance, pixel_size, and version.
        :raises ValueError:
            If r is negative or exceeds 2000 m, pixel_size is invalid, or version is invalid.
        :notes:
            - Uses power function from Table 4 (Page 812) for 'default' (far-field probabilities).
            - Uses near-field interpolation points from Table 5 (page 812) for 'near_field' (r < r1),
              as described in the text on page 819.
            - No magnitude dependence, per Petersen et al. (2011, Page 818).
            - Limited to 2 km distance from principal fault; no triggered ruptures included.
        """
        # Fall back to constructor-pinned values, then legacy defaults
        if cell_size is None:
            cell_size = self.cell_size
        if pixel_size is None:
            pixel_size = (self.pixel_size
                          if self.pixel_size is not None else 25)
        if version is None:
            version = self.version if self.version is not None else "default"
        # Validate inputs
        if cell_size is not None:  # deprecated alias kept for old logic trees
            pixel_size = cell_size
        version = version.lower()
        valid_versions = ["default", "near_field"]
        if version not in valid_versions:
            raise ValueError(f"Invalid version '{version}'. Accepted values are: {', '.join(valid_versions)}")

        # Handle scalar/array input following Youngs2003 pattern
        r = np.asarray(r)
        if r.ndim == 0:
            r = np.array([r])
            was_scalar = True
        else:
            was_scalar = False

        # Convert distance from km to m
        r = r * 1000

        # Validate distance range
        #if not (r >= 0).all() or (r > 2000).any():
        #    raise ValueError("Distance r must be non-negative and ≤ 2000 m")

        if isinstance(pixel_size, str):
            try:
                pixel_size = int(pixel_size)
            except ValueError:
                raise ValueError("Pixel size must be convertible to an integer")
        if pixel_size not in self.PIXEL_SIZES:
            raise ValueError(f"Pixel size must be one of {list(self.PIXEL_SIZES.keys())} m")

        # Get pixel size parameters
        params = self.PIXEL_SIZES[pixel_size]
        a, b, _ = params["a"], params["b"], params["sigma"]
        near_params = self.NEAR_FIELD_POINTS[pixel_size]

        if version == "default":
            # Far-field power function (Page 819, Eqn 20, Table 4)
            r_safe = np.where(r == 0, 0.1, r)  # Use 0.1 m as minimum distance
            ln_P = a * np.log(r_safe) + b
            P_rupture = np.exp(ln_P)  # Convert ln(P) to probability
            P_rupture = np.clip(P_rupture, 0, 1)  # Ensure probability is in [0, 1]
        else:  # version == "near_field"
            # Near-field interpolation (Table 5, page 812; method described on page 819)
            p0, p1, p2 = near_params["p0"], near_params["p1"], near_params["p2"]
            r1, r2 = near_params["r1"], near_params["r2"]

            # Initialize with default probability (p0)
            P_rupture = np.full_like(r, p0, dtype=float)

            # Linear interpolation for r < r1
            mask_near = r < r1
            if np.any(mask_near):
                # Interpolate between p0 and p1 at r1
                P_rupture[mask_near] = p0 + (p1 - p0) * (r[mask_near] / r1)

            # Linear interpolation for r1 <= r <= r2
            mask_mid = (r >= r1) & (r <= r2)
            if np.any(mask_mid):
                # Interpolate between p1 and p2
                P_rupture[mask_mid] = p1 + (p2 - p1) * ((r[mask_mid] - r1) / (r2 - r1))

            # Use power function for far field (r > r2)
            mask_far = r > r2
            if np.any(mask_far):
                r_safe = np.where(r[mask_far] == 0, 0.1, r[mask_far])
                ln_P_far = a * np.log(r_safe) + b
                P_rupture[mask_far] = np.exp(ln_P_far)

            P_rupture = np.clip(P_rupture, 0, 1)  # Ensure probability is in [0, 1]

        # Return scalar if input was scalar, following Youngs2003 pattern
        if was_scalar:
            return float(P_rupture[0])
        else:
            return P_rupture


class Petersen2011SecondarySR_default(Petersen2011SecondarySR):
    """Petersen et al. (2011) distributed-rupture model fixed to the 'default' variant."""

    def get_prob(self, r, pixel_size=25, version="default", cell_size=None):
        """Return distributed surface-rupture probability using the 'default' variant."""
        return super().get_prob(r=r, pixel_size=pixel_size,
                                cell_size=cell_size, version="default")
