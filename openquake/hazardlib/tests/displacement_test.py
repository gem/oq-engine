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

"""Tests for the PFD rate kernel."""
from types import SimpleNamespace

import numpy as np
import pytest

from openquake.hazardlib.calc.displacement import (
    location_weight, calc_rupture_contribution, calc_rates,
    collapse_downdip, SurfaceRuptures, FLOATING_CODES)
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.source import (
    ComplexFaultSource, SimpleFaultSource)
from openquake.hazardlib.tom import PoissonTOM


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


def test_contribution_gaussian_complementary_split():
    ctx = FakeCtx([0.0, 0.5, 0.9, 2.5])
    adapters = {
        'primary_sr': FakeAdapter(sr=1.0),
        'primary_fd': FakeAdapter(fd=0.5),
        'secondary_sr': FakeAdapter(sr=0.8),
        'secondary_fd': FakeAdapter(fd=0.3),
    }
    principal, distributed = calc_rupture_contribution(
        ctx, adapters, IMLS, r_threshold_km=0.1, r_sigma_km=1.0)
    wp = np.exp(-ctx.rtor ** 2 / 2.0)
    wp[3] = 0.0  # truncated beyond 2 sigma
    # principal = rate * P_fd * W_p ; distributed = rate * 0.8*0.3 * (1 - W_p)
    np.testing.assert_allclose(
        principal, 2 * 0.5 * wp[:, None] * np.ones((4, 2)), rtol=1e-15)
    np.testing.assert_allclose(
        distributed, 2 * 0.8 * 0.3 * (1 - wp)[:, None] * np.ones((4, 2)),
        rtol=1e-15)
    assert np.all(distributed[0] == 0.0)  # on the trace G = 0


def _excluding_adapter(r_min_km):
    adapter = FakeAdapter(fd=0.3)
    adapter.model.APPLICABILITY_RANGE = {'r_min_km': r_min_km}
    return adapter


def test_declared_near_trace_exclusion_zeroes_distributed():
    """Visini-style r_min_km: the distributed regression is undefined
    inside it, so those sites keep the principal term only."""
    ctx = FakeCtx([0.0, 0.004, 0.006, 0.5])
    adapters = {
        'primary_fd': FakeAdapter(fd=0.5),
        'secondary_sr': FakeAdapter(sr=0.8),
        'secondary_fd': _excluding_adapter(0.005),
    }
    principal, distributed = calc_rupture_contribution(
        ctx, adapters, IMLS, r_threshold_km=0.1, r_sigma_km=1.0)
    wp = np.exp(-ctx.rtor ** 2 / 2.0)
    expected = 2 * 0.8 * 0.3 * (1 - wp)[:, None] * np.ones((4, 2))
    expected[:2] = 0.0  # |r| < 5 m
    np.testing.assert_allclose(distributed, expected, rtol=1e-15)
    np.testing.assert_allclose(
        principal, 2 * 0.5 * wp[:, None] * np.ones((4, 2)), rtol=1e-15)


def test_no_declared_exclusion_leaves_distributed_unchanged():
    ctx = FakeCtx([0.004, 0.5])
    adapters = {
        'primary_fd': FakeAdapter(fd=0.5),
        'secondary_sr': FakeAdapter(sr=0.8),
        'secondary_fd': FakeAdapter(fd=0.3),
    }
    _, distributed = calc_rupture_contribution(
        ctx, adapters, IMLS, r_threshold_km=0.1, r_sigma_km=1.0)
    wp = np.exp(-ctx.rtor ** 2 / 2.0)
    np.testing.assert_allclose(
        distributed, 2 * 0.8 * 0.3 * (1 - wp)[:, None] * np.ones((2, 2)),
        rtol=1e-15)


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


# --------------------------------------------------------------------------
# down-dip float: geometry, not a probability
# --------------------------------------------------------------------------
class FakeRup:
    def __init__(self, mag, rate, ztor, name=''):
        self.mag = mag
        self.occurrence_rate = rate
        self.name = name
        self.surface = type(
            'S', (), {'get_top_edge_depth': lambda self, z=ztor: z})()


def _simple_fault(mesh, usd=0., lsd=12., dip=60., aspect=1.5,
                  mags=(5.05, 5.55, 6.05, 6.55, 7.05)):
    mfd = EvenlyDiscretizedMFD(
        mags[0], 0.5, [1E-2 / (i + 1) for i in range(len(mags))])
    return SimpleFaultSource(
        'F', 'floating', 'Active Shallow Crust', mfd, mesh, WC1994(),
        aspect, PoissonTOM(1.), usd, lsd,
        Line([Point(10.0, 45.0), Point(10.4, 45.1)]), dip, -90.)


def _rates_by_mag(rups):
    out = {}
    for rup in rups:
        out[rup.mag] = out.get(rup.mag, 0.) + rup.occurrence_rate
    return out


def test_collapse_downdip_fake_ruptures():
    rups = [
        # magnitude 6: 2 positions at the surface with rates 1:3, 2 buried
        FakeRup(6., 1., 0., 'a'), FakeRup(6., 3., 0.005, 'b'),
        FakeRup(6., 2., 1., 'c'), FakeRup(6., 2., 2., 'd'),
        # magnitude 7: the only position is at the surface
        FakeRup(7., 5., 0., 'e'),
        # magnitude 5: never at the surface
        FakeRup(5., .5, 3., 'f'), FakeRup(5., .25, 4., 'g')]
    surf, blind = collapse_downdip(rups, depth_tolerance_km=0.01)
    assert [rup.name for rup in surf] == ['a', 'b', 'e']
    # the whole rate of magnitude 6 (8), split 1:3 as the surface positions
    np.testing.assert_allclose(
        [rup.occurrence_rate for rup in surf], [2., 6., 5.])
    assert blind == {5.: .75}


@pytest.mark.parametrize('mesh', [0.5, 1., 2., 4.])
def test_collapse_downdip_conserves_the_magnitude_rates(mesh):
    # the rate of each magnitude must not depend on the mesh, while the
    # fraction of float positions at the surface does
    src = _simple_fault(mesh)
    mfd_rates = dict(src.get_annual_occurrence_rates())
    allrups = list(src.iter_ruptures())
    n_all = len(allrups)
    at_surface = sum(rup.occurrence_rate for rup in allrups
                     if rup.surface.get_top_edge_depth() <= 0.01)
    surf = SurfaceRuptures(src, 0.01)
    rups = list(surf.iter_ruptures())
    assert surf.blind == {}
    assert len(rups) < n_all
    for rup in rups:
        assert rup.surface.get_top_edge_depth() <= 0.01
        assert rup.surface.original_dip == 60.
    rates = _rates_by_mag(rups)
    assert sorted(rates) == sorted(mfd_rates)
    for mag, rate in mfd_rates.items():
        np.testing.assert_allclose(rates[mag], rate, rtol=1E-12)
    # the bug: the surface fraction acted as a (mesh-dependent) probability
    assert at_surface < 0.8 * sum(mfd_rates.values())
    # the bottom of the source, not of the (shallower) collapsed ruptures
    assert surf.lower_depth == 12.


def test_surface_fraction_depends_on_the_mesh():
    # documents why the fraction N_surf / N_total cannot be a probability
    fractions = []
    for mesh in (0.5, 1., 2., 4.):
        src = _simple_fault(mesh, mags=(5.55,))
        rups = list(src.iter_ruptures())
        n_surf = sum(rup.surface.get_top_edge_depth() <= 0.01
                     for rup in rups)
        fractions.append(n_surf / len(rups))
    assert len(set(np.round(fractions, 6))) == 4
    assert max(fractions) > 2 * min(fractions)


def test_collapse_downdip_keeps_the_along_strike_float():
    # the surface positions are the same and equally likely
    src = _simple_fault(1., mags=(6.05,))
    before = [rup for rup in src.iter_ruptures()
              if rup.surface.get_top_edge_depth() <= 0.01]
    after = list(SurfaceRuptures(src, 0.01).iter_ruptures())
    assert len(after) == len(before) > 1
    for rup0, rup1 in zip(before, after):
        np.testing.assert_array_equal(rup0.surface.mesh.lons,
                                      rup1.surface.mesh.lons)
        np.testing.assert_array_equal(rup0.surface.mesh.depths,
                                      rup1.surface.mesh.depths)
    rates = np.array([rup.occurrence_rate for rup in after])
    np.testing.assert_allclose(rates, 1E-2 / len(after), rtol=1E-12)


def test_collapse_downdip_with_hypocentre_lists():
    # several ruptures per float position (hypocentre x slip), unequal
    # weights: the rates are still conserved magnitude by magnitude
    hypos = np.array([[0.25, 0.25, 0.3], [0.75, 0.5, 0.7]])
    slips = np.array([[90., 1.]])
    mfd = EvenlyDiscretizedMFD(5.55, 0.5, [1E-2, 5E-3])
    src = SimpleFaultSource(
        'F', 'floating', 'Active Shallow Crust', mfd, 1., WC1994(), 1.5,
        PoissonTOM(1.), 0., 12.,
        Line([Point(10.0, 45.0), Point(10.4, 45.1)]), 60., -90.,
        SimpleNamespace(hypo_list=hypos, slip_list=slips, depth_list=[]))
    rups = list(SurfaceRuptures(src, 0.01).iter_ruptures())
    rates = _rates_by_mag(rups)
    for mag, rate in src.get_annual_occurrence_rates():
        np.testing.assert_allclose(rates[mag], rate, rtol=1E-12)
    weights = sorted({round(rup.occurrence_rate / rups[0].occurrence_rate, 6)
                      for rup in rups if rup.mag == rups[0].mag})
    assert len(weights) == 2  # the 0.3 / 0.7 hypocentre weights survive


def test_blind_source_gives_no_surface_ruptures():
    # upper seismogenic depth of 2 km: the geometry declares the source
    # blind, there is no top edge at the surface to carry the hazard
    src = _simple_fault(1., usd=2., lsd=14.)
    surf = SurfaceRuptures(src, 0.01)
    assert list(surf.iter_ruptures()) == []
    total = sum(rate for _mag, rate in src.get_annual_occurrence_rates())
    np.testing.assert_allclose(sum(surf.blind.values()), total)
    assert len(surf.blind) == 5


def test_tolerance_selects_the_geometry_only():
    # with a tolerance deeper than the second row of the mesh both rows
    # carry the rate: more ruptures, same total rate
    src = _simple_fault(1., mags=(5.55,))
    one = list(SurfaceRuptures(src, 0.01).iter_ruptures())
    two = list(SurfaceRuptures(src, 0.9).iter_ruptures())
    assert len(two) == 2 * len(one)
    np.testing.assert_allclose(sum(r.occurrence_rate for r in one), 1E-2)
    np.testing.assert_allclose(sum(r.occurrence_rate for r in two), 1E-2)


def test_collapse_downdip_complex_fault():
    edges = [Line([Point(10.0, 45.0, 0.), Point(10.4, 45.0, 0.)]),
             Line([Point(10.0, 44.95, 8.), Point(10.4, 44.95, 9.)]),
             Line([Point(10.0, 44.9, 15.), Point(10.4, 44.9, 17.)])]
    mfd = EvenlyDiscretizedMFD(5.55, 0.5, [1E-2, 5E-3, 1E-3])
    src = ComplexFaultSource(
        'C', 'complex', 'Active Shallow Crust', mfd, 2., WC1994(), 1.5,
        PoissonTOM(1.), edges, -90.)
    assert src.code in FLOATING_CODES
    n_all = src.count_ruptures()
    surf = SurfaceRuptures(src, 0.01)
    rups = list(surf.iter_ruptures())
    assert 0 < len(rups) < n_all
    rates = _rates_by_mag(rups)
    for mag, rate in src.get_annual_occurrence_rates():
        np.testing.assert_allclose(rates[mag], rate, rtol=1E-12)
    assert surf.lower_depth == 17.  # the deepest point of the edges
    for rup in rups:  # no declared dip: the dip of the rupture is used
        assert not hasattr(rup.surface, 'original_dip')


def test_surface_ruptures_is_a_view_of_the_source():
    src = _simple_fault(2.)
    surf = SurfaceRuptures(src, 0.01)
    assert surf.source_id == 'F' and surf.code == src.code
    assert surf.rake == -90.
    assert getattr(surf, 'location', None) is None
    with pytest.raises(AttributeError):
        surf.missing_attribute
