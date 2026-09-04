# The Hazard Library
# Copyright (C) 2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from types import SimpleNamespace

import numpy
import pytest
from pyproj import Transformer

from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor, RegularGridLayout)
from openquake.hazardlib.correlation_models.local_kriging import (
    LocalKrigingFactor)
from openquake.hazardlib.correlation_models.spatial_cross_imt.du_ning_2021 \
    import DuNing2021
from openquake.hazardlib.imt import PGA, SA


IMTS = [PGA(), SA(0.3)]


def geographic_sites(x, y):
    """Return geographic sites for projected UTM coordinates."""
    transformer = Transformer.from_crs(32610, 4326, always_xy=True)
    x = numpy.asarray(x, dtype=float)
    y = numpy.asarray(y, dtype=float)
    if len(x) == 1:
        lon, lat = transformer.transform(float(x[0]), float(y[0]))
        lons, lats = numpy.array([lon]), numpy.array([lat])
    else:
        lons, lats = transformer.transform(x, y)
    return SimpleNamespace(lons=numpy.asarray(lons), lats=numpy.asarray(lats))


def grid_sites(shape):
    rows, columns = numpy.indices(shape)
    return geographic_sites(
        500_000 + columns.ravel() * 1_000,
        4_200_000 + rows.ravel() * 1_000)


def projected_points(sites):
    transformer = Transformer.from_crs(4326, 32610, always_xy=True)
    x, y = transformer.transform(sites.lons, sites.lats)
    return numpy.column_stack((numpy.asarray(y), numpy.asarray(x))) / 1_000


def distances(first, second):
    differences = first[:, numpy.newaxis] - second[numpy.newaxis, :]
    return numpy.linalg.norm(differences, axis=-1)


def test_exact_local_distribution():
    # An order-two neighborhood covers this complete 4 x 4 grid. Sampling
    # two stations in the same box is therefore identical to constructing
    # their full dense joint covariance with the grid.
    model = DuNing2021()
    grid = grid_sites((4, 4))
    stations = geographic_sites(
        [501_000, 501_300, 501_700],
        [4_201_000, 4_201_200, 4_201_800])
    layout = RegularGridLayout.from_sites(grid)
    ce = CirculantEmbeddingFactor.build(
        model, IMTS, layout.grid_shape, layout.spacing,
        ResidualComponent.WITHIN_EVENT)
    local = LocalKrigingFactor.build(
        model, IMTS, layout, stations, order=2,
        component=ResidualComponent.WITHIN_EVENT)

    total_inputs = ce.input_size + local.error_size
    basis = numpy.eye(total_inputs)
    grid_fields = ce.apply(basis[:ce.input_size]).reshape(
        len(IMTS), -1, total_inputs)
    station_fields = local.apply(
        grid_fields, basis[ce.input_size:])
    applied = numpy.concatenate(
        (grid_fields.reshape(len(IMTS) * len(grid.lons), total_inputs),
         station_fields.reshape(
             len(IMTS) * len(stations.lons), total_inputs)))

    grid_points = projected_points(grid)
    station_points = projected_points(stations)
    all_points = numpy.concatenate((grid_points, station_points))
    full = model.correlation_block(
        distances(all_points, all_points), IMTS,
        component=ResidualComponent.WITHIN_EVENT)
    grid_count = len(grid.lons)
    indices = numpy.concatenate([
        numpy.arange(m * len(all_points), m * len(all_points) + grid_count)
        for m in range(len(IMTS))] + [
        numpy.arange(m * len(all_points) + grid_count,
                     (m + 1) * len(all_points))
        for m in range(len(IMTS))])
    expected = full[numpy.ix_(indices, indices)]
    numpy.testing.assert_allclose(
        applied @ applied.T, expected, atol=2E-12)


def test_grid_padding_required():
    model = DuNing2021()
    grid = grid_sites((4, 4))
    edge_station = geographic_sites([500_300], [4_200_400])
    layout = RegularGridLayout.from_sites(grid)

    with pytest.raises(ValueError, match='expand it'):
        LocalKrigingFactor.build(
            model, IMTS, layout, edge_station, order=2)

    expanded = layout.expanded(edge_station, margin=2)
    factor = LocalKrigingFactor.build(
        model, IMTS, expanded, edge_station, order=2)
    assert factor.error_size == len(IMTS)
    assert factor.groups[0].grid_indices.size == 16


def test_input_shapes():
    model = DuNing2021()
    grid = grid_sites((4, 4))
    stations = geographic_sites([501_300], [4_201_200])
    layout = RegularGridLayout.from_sites(grid)
    factor = LocalKrigingFactor.build(
        model, IMTS, layout, stations, order=2)

    with pytest.raises(ValueError, match='Expected grid fields'):
        factor.apply(numpy.zeros((2, 15, 1)), numpy.zeros((2, 1)))
    with pytest.raises(ValueError, match='Expected local errors'):
        factor.apply(numpy.zeros((2, 16, 1)), numpy.zeros((1, 1)))
