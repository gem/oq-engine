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
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
Sampling of the shake_result.hdf products: the conditional medians and
standard deviations are preserved, the dependence is the one of the
selected correlation models
"""
import os
from types import SimpleNamespace

import h5py
import numpy
import pytest

from openquake.hazardlib.correlation_models.cross_imt.\
    abrahamson_et_al_2014 import AbrahamsonEtAl2014BetweenEvent
from openquake.hazardlib.correlation_models.spatial_cross_imt.\
    loth_baker_2013 import LothBaker2013
from openquake.commonlib.readinput import assoc_to_shakemap
from openquake.hazardlib import site
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.regular_grid import regular_grid
from openquake.hazardlib.shakemap.gmfs import (
    to_gmfs, circulant_embedding_feasible)
from openquake.hazardlib.shakemap.maps import get_sitecol_shakemap
from openquake.hazardlib.shakemap.parsers import get_array_usgs_id
from openquake.hazardlib.shakemap import parsers

DATA = os.path.join(os.path.dirname(__file__), 'data')
# a 10x10 window of the us6000t7uu product (shakemap-modules 1.1.16),
# where the stations reduce the uncertainty the most
REAL = os.path.join(DATA, 'us6000t7uu_shake_result.hdf')
GROUP = 'arrays/imts/GREATER_OF_TWO_HORIZONTAL'


def test_real_product_tau_is_conditional():
    # the stored tau is the conditional between-event std, i.e. the
    # square root of the diagonal of C @ Sigma_HH_YD @ C.T, so that
    # std^2 - tau^2 is the conditional within-event variance; the
    # stored phi is the prior one and exceeds the conditional std
    uri = {'kind': 'shake_result_hdf', 'fname': REAL}
    _, shakemap, *_ = get_sitecol_shakemap(uri, ['PGA', 'SA(1.0)'])
    assert {'tau'} == set(shakemap.dtype.names) - {
        'lon', 'lat', 'vs30', 'val', 'std'}
    with h5py.File(REAL) as h5:
        for im in ('PGA', 'SA(1.0)'):
            group = h5[f'{GROUP}/{im}']
            C = group['C'][()].astype(float)
            C = C.reshape(-1, C.shape[-1])
            tau = numpy.sqrt(numpy.einsum(
                'ij,jk,ik->i', C, group['Sigma_HH_YD'][()], C))
            numpy.testing.assert_allclose(
                shakemap['tau'][im], tau, rtol=1E-5)
            assert (group['phi'][()] > group['std'][()]).all()
            numpy.testing.assert_allclose(
                shakemap['val'][im],
                numpy.exp(group['mean'][()].ravel()) * 100, rtol=1E-5)


@pytest.mark.parametrize('strategy', ['circulant_embedding',
                                      'cholesky_decomposition'])
def test_real_product_preserves_the_marginals(strategy):
    # as in impact mode, the ShakeMap is associated to a regular square
    # grid of sites, here with a spacing of 1 km; the median and the
    # variance of the log GMFs are the conditional ones of ShakeMap
    uri = {'kind': 'shake_result_hdf', 'fname': REAL}
    _, points, *_ = get_sitecol_shakemap(uri, ['PGA', 'SA(1.0)'])
    grid = regular_grid(Mesh(points['lon'], points['lat']), 1, padding=0)
    sites = site.SiteCollection.from_points(grid.lons, grid.lats)
    sitecol, shakemap, _, names = get_sitecol_shakemap(
        uri, ['PGA', 'SA(1.0)'], sites, assoc_dist=1)
    assert circulant_embedding_feasible(sitecol)
    method = {'kind': 'Silva&Horspool', 'spatial_model': LothBaker2013(),
              'cross_imt_model': None, 'cholesky_limit': 10000,
              'between_event_model': AbrahamsonEtAl2014BetweenEvent(),
              'correlation_strategy': strategy, 'sites': sitecol}
    _, gmfs = to_gmfs(shakemap, method, None, 99, 5000, 42, names)
    for i, im in enumerate(names):
        logs = numpy.log(gmfs[:, :, i])
        numpy.testing.assert_allclose(
            logs.var(axis=1), shakemap['std'][im] ** 2, rtol=.08)
        numpy.testing.assert_allclose(
            logs.mean(axis=1), numpy.log(shakemap['val'][im] / 100),
            atol=.025)


class _Assets(list):
    def remap_sites(self, sitecol):
        self.original_sids = sitecol.sids.copy()


def test_assoc_to_shakemap_keeps_the_grid():
    # Keep the original grid for circulant embedding when the reduced site
    # collection is reindexed for storage.
    uri = {'kind': 'shake_result_hdf', 'fname': REAL}
    _, points, *_ = get_sitecol_shakemap(uri, ['PGA'])
    grid = regular_grid(Mesh(points['lon'], points['lat']), 1, padding=0)
    complete = site.SiteCollection.from_points(grid.lons, grid.lats)
    haz_sitecol = complete.filtered([3, 11, 40, 41, 77])  # with assets
    oq = SimpleNamespace(imtls={'PGA': [.1]}, shakemap_id=None, inputs={},
                         shakemap_uri=uri,
                         asset_hazard_distance={'default': 1})
    assetcol = _Assets()
    sitecol, _, haz_sites = assoc_to_shakemap(oq, haz_sitecol, assetcol)
    assert sitecol.complete is sitecol
    assert list(sitecol.sids) == [0, 1, 2, 3, 4]
    assert haz_sites.complete is complete
    assert list(haz_sites.sids) == [3, 11, 40, 41, 77]
    numpy.testing.assert_array_equal(assetcol.original_sids, haz_sites.sids)
    numpy.testing.assert_array_equal(haz_sites.lons, sitecol.lons)
    assert circulant_embedding_feasible(haz_sites)
    assert not circulant_embedding_feasible(sitecol)


def test_unused_imt_without_tau(tmp_path, caplog):
    # an IMT without tau (here an MMI group with only mean and std) drops
    # tau only if it is required
    path = tmp_path / 'shake_result.hdf'
    with h5py.File(REAL) as src, h5py.File(path, 'w') as h5:
        for key in ('dictionaries', 'arrays/vs30'):
            src.copy(key, h5, key)
        for im in ('PGA', 'SA(1.0)'):
            for field in ('mean', 'std', 'tau'):
                h5[f'{GROUP}/{im}/{field}'] = src[f'{GROUP}/{im}/{field}'][()]
        h5[f'{GROUP}/MMI/mean'] = numpy.full((10, 10), 5.)
        h5[f'{GROUP}/MMI/std'] = numpy.full((10, 10), .5)
    uri = {'kind': 'shake_result_hdf', 'fname': str(path)}
    _, shakemap, *_ = get_sitecol_shakemap(uri, ['PGA', 'SA(1.0)'])
    assert 'tau' in shakemap.dtype.names
    _, shakemap, *_ = get_sitecol_shakemap(uri, ['MMI'])
    assert 'tau' not in shakemap.dtype.names
    assert 'The ShakeMap has no tau for MMI' in caplog.text


def _fallback(monkeypatch, exc):
    # get_array_usgs_id with a failing shake_result.hdf and a grid.xml
    xml = numpy.zeros(2, [('lon', float), ('lat', float)])

    def get_array(kind, **kw):
        if kind == 'shake_result_hdf':
            raise exc
        return xml
    monkeypatch.setattr(parsers, 'get_array', get_array)
    contents = {'download/shake_result.hdf': {'url': 'hdf'},
                'download/grid.xml': {'url': 'xml'}}
    return get_array_usgs_id('usgs_id', 'us0', contents)


def test_unreadable_product_falls_back_to_xml(monkeypatch, caplog):
    array = _fallback(monkeypatch, OSError('truncated file'))
    assert array.dtype.names == ('lon', 'lat')
    assert 'falling back to grid.xml' in caplog.text


def test_errors_are_not_hidden_by_the_xml_fallback(monkeypatch):
    with pytest.raises(ValueError, match='a bug'):
        _fallback(monkeypatch, ValueError('a bug'))
