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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Engine-context wiring for the FDHA model adapter (PR-4 of the oq-engine
integration plan).

The adapter's ctx->model translation originally assumed the oq-pfdha
``FDHAContext`` protocol (``metrics_for`` and a derived ``style`` array).
These tests pin the engine wiring: a hazardlib
:class:`~openquake.hazardlib.contexts.RuptureContext` carrying the PR-3
fields (``rtor``, ``x_l``, ``length``, ``rx``) drives the distance-dependent
models, and the faulting style is derived from ``rake``.
"""
import numpy as np
import pytest

from openquake.hazardlib.contexts import RuptureContext
from openquake.pfd.adapter import (
    LegacyModelAdapter, style_from_rake, NEAR_FIELD_FLOOR_KM)
from openquake.pfd.secondary_surf_displ.youngs2003 import (
    Youngs2003SecondaryFD)
from openquake.pfd.secondary_surf_rup.youngs2003 import (
    Youngs2003SecondarySR)


def make_ctx(n=3, mag=6.5, dip=60.0, rake=90.0, length=30.0,
             rtor=(0.1, 0.5, 1.0), x_l=(0.2, 0.5, 0.8),
             rx=(0.1, -0.5, 1.0), vs30=(760.0, 760.0, 760.0)):
    """A hazardlib RuptureContext with the PR-3 FDHA distance fields."""
    ctx = RuptureContext()
    ctx.sids = np.arange(n, dtype=np.uint32)
    ctx.mag = np.full(n, float(mag))
    ctx.dip = np.full(n, float(dip))
    ctx.rake = np.full(n, float(rake))
    ctx.length = np.full(n, float(length))
    ctx.rtor = np.asarray(rtor, dtype=float)
    ctx.x_l = np.asarray(x_l, dtype=float)
    ctx.rx = np.asarray(rx, dtype=float)
    ctx.vs30 = np.asarray(vs30, dtype=float)
    return ctx


class _SecondaryFDStub:
    """Records the kwargs the adapter passes to a distributed FD model."""
    DISPLACEMENT_DEFINITION = "distributed"
    MULTIFAULT_REFERENCE_LINE = "lcp"
    NEAR_FIELD_FLOOR = None

    def get_prob(self, d, mag, r, rx, s=None, X_L_ratio=None, x_L=None,
                 dip=None, L=None, style=None, **kw):
        self.seen = dict(d=np.asarray(d), mag=mag, r=np.asarray(r),
                         rx=np.asarray(rx), x_L=np.asarray(x_L),
                         L=np.asarray(L), style=style)
        return np.zeros((len(self.seen['r']), len(self.seen['d'])))


class _PrimaryFDStub:
    """Records the kwargs the adapter passes to a primary FD model."""
    DISPLACEMENT_DEFINITION = "principal"
    MULTIFAULT_REFERENCE_LINE = "lcp"

    def get_prob(self, d, X_L_ratio, mag, x_L=None, style=None, **kw):
        self.seen = dict(d=np.asarray(d), X_L_ratio=np.asarray(X_L_ratio),
                         x_L=np.asarray(x_L), mag=mag, style=style)
        return np.zeros((len(self.seen['X_L_ratio']), len(self.seen['d'])))


class _SecondarySRStub:
    """Records the kwargs the adapter passes to a distributed SR model."""
    MULTIFAULT_REFERENCE_LINE = "segments"

    def get_prob(self, mag, rx, r, style=None, **kw):
        self.seen = dict(mag=mag, r=np.asarray(r), rx=np.asarray(rx),
                         style=style)
        return np.zeros(len(self.seen['r']))


@pytest.mark.parametrize("rake,expected", [
    (0.0, 'strike-slip'), (180.0, 'strike-slip'), (151.0, 'strike-slip'),
    (90.0, 'reverse'), (45.0, 'reverse'), (150.0, 'reverse'),
    (-90.0, 'normal'), (-45.0, 'normal'), (-150.0, 'normal'),
])
def test_style_from_rake(rake, expected):
    assert style_from_rake(rake) == expected


def test_secondary_fd_uses_engine_distance_fields():
    model = _SecondaryFDStub()
    adapter = LegacyModelAdapter(model)
    ctx = make_ctx()
    d = np.array([0.01, 0.1, 1.0])
    out = adapter.compute_secondary_fd(ctx, d, {'method': 'median', 'q': 50})
    assert out.shape == (3, 3)
    # r / x_L / L come from rtor / x_l / length; rx is passed through
    np.testing.assert_array_equal(model.seen['r'], ctx.rtor)
    np.testing.assert_array_equal(model.seen['x_L'], ctx.x_l)
    np.testing.assert_array_equal(model.seen['L'], ctx.length)
    np.testing.assert_array_equal(model.seen['rx'], ctx.rx)
    # style is derived from rake (=90 -> reverse)
    assert model.seen['style'] == 'reverse'


def test_primary_fd_uses_engine_x_l():
    model = _PrimaryFDStub()
    adapter = LegacyModelAdapter(model)
    ctx = make_ctx()
    d = np.array([0.01, 0.1])
    out = adapter.compute_primary_fd(ctx, d, {'method': 'median', 'q': 50})
    assert out.shape == (3, 2)
    np.testing.assert_array_equal(model.seen['X_L_ratio'], ctx.x_l)
    np.testing.assert_array_equal(model.seen['x_L'], ctx.x_l)
    assert model.seen['style'] == 'reverse'


def test_secondary_sr_uses_engine_rtor():
    model = _SecondarySRStub()
    adapter = LegacyModelAdapter(model)
    ctx = make_ctx()
    out = adapter.compute_secondary_sr(ctx, {'method': 'median', 'q': 50})
    assert out.shape == (3,)
    np.testing.assert_array_equal(model.seen['r'], ctx.rtor)
    np.testing.assert_array_equal(model.seen['rx'], ctx.rx)
    assert model.seen['style'] == 'reverse'


def test_near_field_floor_clamps_only_declaring_models():
    class _PetersenStub(_SecondaryFDStub):
        NEAR_FIELD_FLOOR = "footprint_half"

    ctx = make_ctx(rtor=(0.0, 0.005, 0.5))
    d = np.array([0.1])

    clamped = _PetersenStub()
    LegacyModelAdapter(clamped).compute_secondary_fd(
        ctx, d, {'method': 'median', 'q': 50})
    np.testing.assert_allclose(
        clamped.seen['r'], [NEAR_FIELD_FLOOR_KM, NEAR_FIELD_FLOOR_KM, 0.5])

    bounded = _SecondaryFDStub()
    LegacyModelAdapter(bounded).compute_secondary_fd(
        ctx, d, {'method': 'median', 'q': 50})
    np.testing.assert_allclose(bounded.seen['r'], [0.0, 0.005, 0.5])


class _ProtoCtx:
    """Context exposing the native FDHAContext ``metrics_for`` protocol."""
    MULTIFAULT = None

    def __init__(self, r, x_l, length):
        self._metrics = (np.asarray(r, dtype=float),
                         np.asarray(x_l, dtype=float),
                         np.asarray(length, dtype=float))
        n = len(self._metrics[0])
        self.sids = np.arange(n, dtype=np.uint32)
        self.mag = np.full(n, 6.5)
        self.dip = np.full(n, 60.0)
        self.rake = np.full(n, 0.0)
        self.rx = np.zeros(n)
        self.vs30 = np.full(n, 760.0)

    def __len__(self):
        return len(self.sids)

    def metrics_for(self, method):
        return self._metrics


def test_metrics_for_protocol_takes_precedence():
    model = _SecondarySRStub()
    model.MULTIFAULT_REFERENCE_LINE = 'segments'
    adapter = LegacyModelAdapter(model)
    ctx = _ProtoCtx(r=[1.0, 2.0], x_l=[0.25, 0.75], length=[10.0, 10.0])
    adapter.compute_secondary_sr(ctx, {'method': 'median', 'q': 50})
    np.testing.assert_array_equal(model.seen['r'], [1.0, 2.0])


def test_ref_metrics_mapping_takes_precedence():
    model = _SecondarySRStub()
    model.MULTIFAULT_REFERENCE_LINE = 'segments'
    adapter = LegacyModelAdapter(model)
    ctx = make_ctx(rtor=(9.0, 9.0, 9.0))
    ctx.ref_metrics = {'segments': {
        'r': np.array([1.0, 2.0, 3.0]),
        'x_L': np.array([0.1, 0.2, 0.3]),
        'L': np.array([10.0, 10.0, 10.0])}}
    adapter.compute_secondary_sr(ctx, {'method': 'median', 'q': 50})
    np.testing.assert_array_equal(model.seen['r'], [1.0, 2.0, 3.0])


def test_secondary_fd_matches_direct_model_call():
    """The adapter's engine-context path reproduces a direct model call."""
    model = Youngs2003SecondaryFD()
    adapter = LegacyModelAdapter(model, {'style': 'all'})
    ctx = make_ctx(rtor=(0.1, 0.5, 1.0), rx=(0.1, -0.5, 1.0))
    d = np.array([0.01, 0.1, 1.0])
    got = adapter.compute_secondary_fd(ctx, d, {'method': 'median', 'q': 50})
    expected = model.get_prob(d=d, mag=6.5, rx=ctx.rx, r=ctx.rtor)
    np.testing.assert_allclose(got, expected, rtol=1e-12)


def test_secondary_sr_matches_direct_model_call():
    model = Youngs2003SecondarySR()
    adapter = LegacyModelAdapter(model, {'style': 'all'})
    ctx = make_ctx(rtor=(0.1, 0.5, 1.0), rx=(0.1, -0.5, 1.0))
    got = adapter.compute_secondary_sr(ctx, {'method': 'median', 'q': 50})
    expected = model.get_prob(mag=6.5, rx=ctx.rx, r=ctx.rtor)
    np.testing.assert_allclose(got, expected, rtol=1e-12)