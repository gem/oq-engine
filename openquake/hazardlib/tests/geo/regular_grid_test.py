# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""Deterministic spacing, coordinate precision and allocation checks."""
from types import SimpleNamespace
from unittest.mock import patch

import numpy
import pytest
from pyproj import Transformer

from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.regular_grid import regular_grid
from openquake.hazardlib.correlation_models.circulant_embedding import (
    RegularGridLayout)


@pytest.mark.parametrize('lons,lats', [
    ([12.2, 12.3], [42, 41.94]),
    ([174.5, 174.8], [-41.2, -41])])
@pytest.mark.parametrize('spacing', [0.5, 1, 2])
def test_spacing(lons, lats, spacing):
    mesh = Mesh(numpy.array(lons), numpy.array(lats))
    grid = regular_grid(mesh, spacing)
    assert grid.lons.dtype == numpy.float64
    again = regular_grid(mesh, spacing)
    numpy.testing.assert_array_equal(grid.lons, again.lons)
    numpy.testing.assert_array_equal(grid.lats, again.lats)
    layout = RegularGridLayout.from_sites(grid)
    assert layout.crs.startswith('+proj=tmerc')
    assert len(grid.lons) == numpy.prod(layout.grid_shape)
    numpy.testing.assert_array_equal(
        layout.site_indices, numpy.arange(len(grid.lons)))
    x, y = Transformer.from_crs(4326, layout.crs, always_xy=True).transform(
        grid.lons, grid.lats)
    x = numpy.asarray(x).reshape(layout.grid_shape)
    y = numpy.asarray(y).reshape(layout.grid_shape)
    # Rows are west to east, ordered south to north, with square cells.
    numpy.testing.assert_allclose(numpy.diff(x, axis=1),
                                  spacing * 1000, atol=1.5)
    numpy.testing.assert_allclose(numpy.diff(y, axis=0),
                                  spacing * 1000, atol=1.5)
    # Five-decimal geographic coordinates have approximately metre precision.
    numpy.testing.assert_allclose(layout.spacing, spacing, atol=0.0015)
    assert layout.maximum_error < 1


def test_padding():
    mesh = Mesh(numpy.array([14.7, 15.1]), numpy.array([41.7, 41.9]))
    grid = regular_grid(mesh, 1)
    layout = RegularGridLayout.from_sites(grid)
    projection = Transformer.from_crs(4326, layout.crs, always_xy=True)
    x, y = numpy.asarray(projection.transform(mesh.lons, mesh.lats))
    lower = numpy.floor((numpy.array([x.min(), y.min()]) - 1000) / 1000)
    upper = numpy.ceil((numpy.array([x.max(), y.max()]) + 1000) / 1000)
    assert layout.grid_shape == tuple((upper - lower + 1).astype(int)[::-1])
    numpy.testing.assert_allclose(
        layout.projected_origin, lower[::-1] * 1000, atol=1)


@pytest.mark.parametrize('spacing', [None, 0, -1, numpy.nan, numpy.inf])
def test_bad_spacing(spacing):
    mesh = Mesh(numpy.array([12.3]), numpy.array([42]))
    with pytest.raises(ValueError, match='Grid spacing'):
        regular_grid(mesh, spacing)


@pytest.mark.parametrize('lons,lats,message', [
    ([], [], 'nonempty'),
    ([12], [], 'matching'),
    ([numpy.nan], [42], 'finite'),
    ([numpy.inf], [42], 'finite'),
    ([181], [42], 'Longitude'),
    ([12], [85], 'latitude'),
    ([12], [-81], 'latitude'),
    ([179.9, -179.9], [42, 42], 'Antimeridian')])
def test_geography(lons, lats, message):
    mesh = SimpleNamespace(lons=numpy.array(lons), lats=numpy.array(lats))
    with pytest.raises(ValueError, match=message):
        regular_grid(mesh, 1)


@pytest.mark.parametrize('spacing,padding', [(0.001, 10), (1, 2000)])
def test_limits(spacing, padding):
    mesh = Mesh(numpy.array([12.3]), numpy.array([42]))
    with patch('numpy.meshgrid') as allocate:
        with pytest.raises(ValueError, match='candidate cells'):
            regular_grid(mesh, spacing, padding)
        allocate.assert_not_called()


def test_zone_boundary():
    # An extent crossing the 36E boundary between UTM zones 36 and 37
    mesh = Mesh(numpy.array([35.5, 36.5, 37.5, 36.0]),
                numpy.array([44, 44.2, 44.1, 44.4]))
    grid = regular_grid(mesh, 5)
    layout = RegularGridLayout.from_sites(grid)
    assert len(grid.lons) == numpy.prod(layout.grid_shape)
    numpy.testing.assert_array_equal(
        layout.site_indices, numpy.arange(len(grid.lons)))


def test_rounding():
    mesh = Mesh(numpy.array([12.3]), numpy.array([42]))
    with pytest.raises(ValueError, match='Duplicate grid cells'):
        regular_grid(mesh, 0.0001)
