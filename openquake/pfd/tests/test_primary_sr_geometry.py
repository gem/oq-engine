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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
The primary surface-rupture probability P(SR | m) is given by exactly one
model. A geometry-based model (Mammarella et al. 2024) must be evaluated
with the dip and the seismogenic depth of the fault that hosts the rupture,
which the adapter reads from the context; the empirical models depend on
the magnitude only.
"""
import numpy as np
import pytest

from openquake.pfd.adapter import PFDModelAdapter, SOURCE_GEOMETRY_PARAMS
from openquake.pfd.primary_surf_rup.fixed import FixedPrimarySR
from openquake.pfd.primary_surf_rup.mammarella2024 import (
    MammarellaEtAl2024PrimarySR)
from openquake.pfd.primary_surf_rup.wells_coppersmith1993 import (
    WellsCoppersmith1993PrimarySR)
from openquake.pfd.primary_surf_rup.youngs2003 import YoungsEtAl2003PrimarySR

RED = {'method': 'mean'}
#: a Mammarella branch that leaves the geometry to the sources
PARAMS = dict(MSR=0, HDD_str='AGG_N', style='normal', dip_sigma=5.,
              t_d=2., Zs_sigma=2., t_z=2.)


class Ctx:
    """A two-site context of one rupture, with or without ``zbot``."""
    def __init__(self, mag, dip, zbot=None, rake=-90.):
        self.mag = np.full(2, mag)
        self.dip = np.full(2, dip)
        self.rake = np.full(2, rake)
        self.vs30 = np.full(2, 760.)
        if zbot is not None:
            self.zbot = np.full(2, zbot)

    def __len__(self):
        return 2


def adapter(**extra):
    params = dict(PARAMS, **extra)
    return PFDModelAdapter(MammarellaEtAl2024PrimarySR(**params), params)


def direct(mag, dip, depth):
    return MammarellaEtAl2024PrimarySR(**PARAMS).get_prob(
        mag, dip_mu=dip, Zs_mu=depth)


@pytest.mark.parametrize('dip,depth', [(60., 12.), (35., 20.), (85., 8.)])
def test_mammarella_uses_the_geometry_of_the_source(dip, depth):
    for mag in (5.5, 6.5, 7.5):
        p_sr = adapter().compute_primary_sr(Ctx(mag, dip, depth), RED)
        assert p_sr.shape == (2,)
        np.testing.assert_allclose(
            p_sr, direct(mag, dip, depth), rtol=1E-12)


def test_mammarella_distinguishes_the_sources():
    # same branch, same magnitude, two different faults
    shallow = adapter().compute_primary_sr(Ctx(6.5, 60., 10.), RED)[0]
    deep = adapter().compute_primary_sr(Ctx(6.5, 60., 20.), RED)[0]
    steep = adapter().compute_primary_sr(Ctx(6.5, 85., 20.), RED)[0]
    # a thinner seismogenic layer is easier to break up to the surface,
    # and for the same depth a steeper fault needs less width
    assert shallow > deep
    assert steep > deep
    # none of them is the old hard-coded 15 km
    old = direct(6.5, 60., 15.)
    assert abs(shallow - old) > 1E-3 and abs(deep - old) > 1E-3


def test_mammarella_has_no_default_depth():
    # without the depth of the source the model must complain, instead of
    # silently assuming a seismogenic thickness
    with pytest.raises(RuntimeError, match='Zs_mu or seismothickness'):
        adapter().compute_primary_sr(Ctx(6.5, 60.), RED)


@pytest.mark.parametrize('name', ['seismothickness', 'Zs_mu'])
def test_a_pinned_depth_wins_and_is_reported(name):
    ad = adapter(**{name: 9.})
    assert ad.pinned_geometry_params() == {name: 9.}
    np.testing.assert_allclose(
        ad.compute_primary_sr(Ctx(6.5, 60., 20.), RED),
        direct(6.5, 60., 9.), rtol=1E-12)
    # also for a context without depth
    np.testing.assert_allclose(
        ad.compute_primary_sr(Ctx(6.5, 60.), RED),
        direct(6.5, 60., 9.), rtol=1E-12)


def test_a_pinned_dip_wins_and_is_reported():
    ad = adapter(dip_mu=75.)
    assert ad.pinned_geometry_params() == {'dip_mu': 75.}
    np.testing.assert_allclose(
        ad.compute_primary_sr(Ctx(6.5, 40., 12.), RED),
        direct(6.5, 75., 12.), rtol=1E-12)


def test_the_unpinned_branch_reports_nothing():
    assert adapter().pinned_geometry_params() == {}
    assert set(SOURCE_GEOMETRY_PARAMS) == {
        'dip_mu', 'Zs_mu', 'seismothickness'}


@pytest.mark.parametrize('model,params', [
    (YoungsEtAl2003PrimarySR, {'style': 'all'}),
    (WellsCoppersmith1993PrimarySR, {}),
    (FixedPrimarySR, {'value': 0.3})])
def test_empirical_models_ignore_the_geometry(model, params):
    ad = PFDModelAdapter(model(**params), params)
    assert ad.pinned_geometry_params() == {}
    probs = [ad.compute_primary_sr(Ctx(6.5, dip, depth, rake=0.), RED)[0]
             for dip, depth in [(30., 8.), (60., 15.), (90., 25.)]]
    assert probs[0] == probs[1] == probs[2]
    assert 0. < probs[0] <= 1.
    # nor do they need it
    assert ad.compute_primary_sr(Ctx(6.5, 60., rake=0.), RED)[0] == probs[0]
