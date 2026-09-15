# -*- coding: utf-8 -*-
"""
Regression tests for the Visini2025SecondaryFD output orientation.

The exceedance matrix must always be (n_sites, n_displ) with displacement
thresholds along columns. The orientation must never be inferred from shape
equality: when a job coincidentally had as many sites as displacement levels,
the old heuristic silently returned the element-wise diagonal (site i paired
with threshold i) instead of the full matrix.
"""
import numpy as np
import pytest

from openquake.pfd.secondary_surf_displ.visini2025 import Visini2025SecondaryFD

pytestmark = [pytest.mark.unit, pytest.mark.visini2025]


D3 = np.array([0.01, 0.1, 1.0])
S4 = np.array([200.0, 500.0, 1000.0, 5000.0])  # metres
KW = dict(mag=6.5, X_L_ratio=0.5, dip=60.0, style="reverse")


def test_square_case_matches_rectangular_reference():
    """n_sites == n_displ must yield the same rows as the unambiguous case."""
    fd = Visini2025SecondaryFD()
    p4 = np.asarray(fd.get_prob(d=D3, s=S4, rx=S4, **KW))
    p3 = np.asarray(fd.get_prob(d=D3, s=S4[:3], rx=S4[:3], **KW))
    assert p4.shape == (4, 3)
    assert p3.shape == (3, 3)
    np.testing.assert_allclose(p3, p4[:3], rtol=1e-12)


def test_rectangular_orientation_is_sites_by_displacements():
    fd = Visini2025SecondaryFD()
    p = np.asarray(fd.get_prob(d=D3, s=S4, rx=S4, **KW))
    assert p.shape == (4, 3)
    # exceedance decreases with threshold (along columns) at fixed site ...
    assert np.all(np.diff(p, axis=1) <= 0)
    # ... and decreases with distance (along rows) at fixed threshold
    assert np.all(np.diff(p, axis=0) <= 0)


def test_scalar_inputs_yield_single_probability():
    # NB: scalar inputs have always produced a squeezable single-element
    # result (get_median_displacement is atleast_1d internally); the shape
    # fix must not change that contract.
    fd = Visini2025SecondaryFD()
    p = np.squeeze(fd.get_prob(d=0.1, mag=6.5, s=500.0, rx=500.0,
                               X_L_ratio=0.5, dip=60.0, style="normal"))
    assert p.shape == ()
    assert 0.0 <= float(p) <= 1.0


def test_single_site_keeps_row_shape():
    fd = Visini2025SecondaryFD()
    p = np.asarray(fd.get_prob(d=D3, s=S4[:1], rx=S4[:1], **KW))
    assert p.shape == (1, 3)
