"""
Unit tests: Youngs2003 x/L folding behavior

Tests the x/L folding symmetry in Youngs2003 model.
"""

import numpy as np
import math
import pytest

from openquake.pfd.primary_surf_displ.youngs2003 import Youngs2003PrimaryFD

pytestmark = pytest.mark.unit


def _fold(model, x):
    # Access folding via get_prob public API
    d = np.array([0.01])  # any positive displacement
    mag = 6.5
    # We call with AD; the returned matrix shape is (1, n_sites)
    P = model.get_prob(d=d, X_L_ratio=np.array([x]), mag=mag, style="normal", norm_disp_type="AD")
    assert P.shape == (1, 1)
    return P[0, 0]


def test_folding_invariant_under_x_to_1_minus_x():
    model = Youngs2003PrimaryFD()
    # Pick several values; folding should make x and 1-x identical
    for x in [0.0, 0.1, 0.25, 0.49]:
        p1 = _fold(model, x)
        p2 = _fold(model, 1.0 - x)
        assert math.isfinite(p1) and math.isfinite(p2)
        assert abs(p1 - p2) <= 1e-12


def test_folding_handles_1_plus_eps_and_minus_eps():
    model = Youngs2003PrimaryFD()
    eps = 1e-15
    p1 = _fold(model, 1.0 + eps)
    p2 = _fold(model, -eps)
    p0 = _fold(model, 0.0)
    # Both should map to boundary behavior near 0
    assert math.isfinite(p1) and math.isfinite(p2) and math.isfinite(p0)
    assert abs(p1 - p0) <= 1e-12
    assert abs(p2 - p0) <= 1e-12


def test_values_at_boundaries_ad_and_md():
    model = Youngs2003PrimaryFD()
    d = np.array([0.01])
    mag = 6.5
    for x in [0.0, 0.5]:
        P_ad = model.get_prob(d=d, X_L_ratio=np.array([x]), mag=mag, style="normal", norm_disp_type="AD")
        P_md = model.get_prob(d=d, X_L_ratio=np.array([x]), mag=mag, style="normal", norm_disp_type="MD")
        assert P_ad.shape == (1, 1)
        assert P_md.shape == (1, 1)
        assert np.isfinite(P_ad).all()
        assert np.isfinite(P_md).all()


