# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""Tests for the PFD rate kernel (PR-6)."""
import numpy as np
import pytest

from openquake.hazardlib.calc.displacement import (
    location_weight, calc_rupture_contribution, calc_rates)


class FakeCtx:
    def __init__(self, rtor, sids=None, rate=2.0):
        self.rtor = np.asarray(rtor, dtype=float)
        n = len(self.rtor)
        self.sids = np.arange(n, dtype=np.int64) if sids is None \
            else np.asarray(sids, dtype=np.int64)
        self.occurrence_rate = np.full(n, float(rate))

    def __len__(self):
        return len(self.rtor)


class FakeAdapter:
    """Adapter stub returning fixed arrays; records nothing."""
    def __init__(self, definition='principal', sr=1.0, fd=0.5):
        self.model = type('M', (), {'DISPLACEMENT_DEFINITION': definition})()
        self.sr = sr
        self.fd = fd  # float -> broadcast over displacement levels

    def compute_primary_sr(self, ctx, red_cfg):
        return np.full(len(ctx), self.sr)

    def compute_primary_fd(self, ctx, imls, red_cfg):
        return np.full((len(ctx), len(imls)), self.fd)

    def compute_secondary_sr(self, ctx, red_cfg):
        return np.full(len(ctx), self.sr)

    def compute_secondary_fd(self, ctx, imls, red_cfg):
        return np.full((len(ctx), len(imls)), self.fd)


IMLS = np.array([0.1, 1.0])


# --------------------------------------------------------------------------
# location weight
# --------------------------------------------------------------------------
def test_location_weight_boxcar():
    r = np.array([0.0, 0.05, 0.1, 0.10001, 0.5])
    np.testing.assert_array_equal(
        location_weight(r, r_threshold_km=0.1, r_sigma_km=0.0),
        [1.0, 1.0, 1.0, 0.0, 0.0])


def test_location_weight_gaussian_pinned_and_truncated():
    sigma = 1.0
    r = np.array([0.0, 0.5, 1.0, 2.0, 2.5])
    wp = location_weight(r, r_threshold_km=0.1, r_sigma_km=sigma)
    assert wp[0] == 1.0                       # pinned on the trace
    assert wp[4] == 0.0                       # truncated beyond +/-2 sigma
    expected = np.exp(-r[:4] ** 2 / (2 * sigma ** 2))
    np.testing.assert_allclose(wp[:4], expected, rtol=1e-15)
    # monotone non-increasing in |r|
    assert np.all(np.diff(wp) <= 0)
    # h plays no role on the Gaussian path
    np.testing.assert_array_equal(
        wp, location_weight(r, r_threshold_km=99.0, r_sigma_km=sigma))


def test_location_weight_symmetric():
    np.testing.assert_array_equal(
        location_weight(np.array([-0.05, 0.05]), 0.1, 0.0), [1.0, 1.0])


# --------------------------------------------------------------------------
# rupture contribution
# --------------------------------------------------------------------------
def test_contribution_boxcar_complementary_split():
    ctx = FakeCtx([0.0, 0.1, 0.5])
    adapters = {
        'primary_sr': FakeAdapter(sr=1.0),
        'primary_fd': FakeAdapter(fd=0.5),
        'secondary_sr': FakeAdapter(sr=1.0),
        'secondary_fd': FakeAdapter(fd=0.3),
    }
    principal, distributed = calc_rupture_contribution(
        ctx, adapters, IMLS, r_threshold_km=0.1, r_sigma_km=0.0)
    # W_p = [1, 1, 0]; G = [0, 0, 1]; rate = 2
    # principal[s, d] = rate * P_fd * W_p[s] (P_fd is level-independent here)
    np.testing.assert_allclose(
        principal, [[1.0, 1.0], [1.0, 1.0], [0.0, 0.0]], rtol=1e-15)
    np.testing.assert_allclose(
        distributed, [[0.0, 0.0], [0.0, 0.0], [0.6, 0.6]], rtol=1e-15)


def test_contribution_gaussian_additive_split():
    ctx = FakeCtx([0.0, 0.5, 0.9])
    adapters = {
        'primary_sr': FakeAdapter(sr=1.0),
        'primary_fd': FakeAdapter(fd=0.5),
        'secondary_sr': FakeAdapter(sr=0.8),
        'secondary_fd': FakeAdapter(fd=0.3),
    }
    principal, distributed = calc_rupture_contribution(
        ctx, adapters, IMLS, r_threshold_km=0.1, r_sigma_km=1.0)
    wp = np.exp(-ctx.rtor ** 2 / 2.0)
    # principal = rate * P_fd * W_p ; distributed = rate * 0.8*0.3 * 1
    np.testing.assert_allclose(
        principal, 2 * 0.5 * wp[:, None] * np.ones((3, 2)), rtol=1e-15)
    np.testing.assert_allclose(
        distributed, 2 * 0.8 * 0.3 * np.ones((3, 2)), rtol=1e-15)


def test_missing_primary_sr_defaults_to_one():
    ctx = FakeCtx([0.0])
    adapters = {'primary_fd': FakeAdapter(fd=1.0)}
    principal, distributed = calc_rupture_contribution(
        ctx, adapters, IMLS, r_threshold_km=0.1, r_sigma_km=0.0)
    np.testing.assert_allclose(principal, [[2.0, 2.0]])
    np.testing.assert_allclose(distributed, [[0.0, 0.0]])


def test_aggregate_model_single_bucket():
    ctx = FakeCtx([0.0, 0.5])
    adapters = {
        'primary_fd': FakeAdapter(definition='aggregate', fd=0.4),
        # a secondary slot would double count; the kernel must ignore it
        'secondary_fd': FakeAdapter(fd=0.9),
    }
    principal, distributed = calc_rupture_contribution(
        ctx, adapters, IMLS, r_threshold_km=0.1, r_sigma_km=0.0)
    np.testing.assert_allclose(
        principal, [[0.8, 0.8], [0.0, 0.0]], rtol=1e-15)
    np.testing.assert_allclose(distributed, np.zeros((2, 2)))


# --------------------------------------------------------------------------
# rate accumulation
# --------------------------------------------------------------------------
def test_calc_rates_accumulates_and_handles_duplicate_sids():
    adapters = {'primary_fd': FakeAdapter(fd=1.0)}
    ctx1 = FakeCtx([0.0, 0.0], sids=[0, 0], rate=1.0)
    ctx2 = FakeCtx([0.0], sids=[0], rate=3.0)
    rates, principal, distributed = calc_rates(
        [ctx1, ctx2], n_sites=2, adapters=adapters, imls=IMLS,
        r_threshold_km=0.1, r_sigma_km=0.0)
    # site 0 gets 1*1 + 1*1 (two rows) + 3*1 = 5 per level; site 1 gets 0
    np.testing.assert_allclose(rates, [[5.0, 5.0], [0.0, 0.0]])
    np.testing.assert_allclose(rates, principal + distributed)


def test_calc_rates_shape_mismatch_raises():
    adapters = {'primary_fd': FakeAdapter(fd=1.0)}
    ctx = FakeCtx([0.0, 0.0], sids=[0])  # 2 rtor rows, 1 sid
    with pytest.raises(ValueError, match="shape mismatch"):
        calc_rates([ctx], n_sites=1, adapters=adapters, imls=IMLS,
                   r_threshold_km=0.1, r_sigma_km=0.0)
