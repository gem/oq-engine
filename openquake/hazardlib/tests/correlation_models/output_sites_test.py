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
from unittest.mock import patch

import numpy
import pytest
from pyproj import Transformer

from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor, RegularGridLayout)
from openquake.hazardlib.correlation_models.local_kriging import (
    LocalKrigingFactor, covariance_root)
from openquake.hazardlib.correlation_models.output_sites import (
    ContinuousDuNing, ContinuousGridFactor, OutputSitesFactor,
    nugget_covariance)
from openquake.hazardlib.correlation_models.spatial_cross_imt.du_ning_2021 \
    import DuNing2021Interpolated
from openquake.hazardlib.imt import PGA, PGV, SA

IMTS = [PGA(), PGV(), SA(0.3), SA(0.6), SA(1.0), SA(3.0)]
CRS = '+proj=tmerc +lon_0=133 +k=1 +datum=WGS84 +units=m'
COMPONENT = ResidualComponent.WITHIN_EVENT


def locations(x, y):
    lons, lats = Transformer.from_crs(CRS, 4326, always_xy=True).transform(
        numpy.asarray(x), numpy.asarray(y))
    return SimpleNamespace(lons=lons, lats=lats, grid_crs=CRS)


def covariance(model, points, imts):
    distances = numpy.linalg.norm(points[:, None] - points[None, :], axis=-1)
    return model.correlation_block(distances, imts, component=COMPONENT)


def implied_covariance(local, model, imts):
    # Use the actual local weights and error roots. CE's grid covariance is
    # checked independently, so no enormous FFT identity basis is required.
    cells = numpy.unique(numpy.concatenate(
        [local.on_grid_cells] + [g.grid_indices for g in local.groups]))
    rows, columns = numpy.divmod(cells, local.layout.grid_shape[1])
    points = numpy.column_stack((rows, columns)) * local.layout.spacing
    M, N, K = len(imts), local.num_stations, len(cells)
    weights = numpy.zeros((M * N, M * K))
    errors = numpy.zeros((M * N, M * N))
    for m in range(M):
        weights[m * N + local.on_grid_stations,
                m * K + numpy.searchsorted(cells, local.on_grid_cells)] = 1
    for group in local.groups:
        selected = numpy.concatenate(
            [m * N + group.station_indices for m in range(M)])
        indices = numpy.searchsorted(cells, group.grid_indices)
        neighbors = numpy.concatenate([m * K + indices for m in range(M)])
        weights[numpy.ix_(selected, neighbors)] = group.weights
        errors[numpy.ix_(selected, selected)] = (
            group.conditional_root @ group.conditional_root.T)
    return weights @ covariance(model, points, imts) @ weights.T + errors


@pytest.mark.parametrize('phase', [0.1, 0.5, 0.9])
@pytest.mark.parametrize('gap', [2., 100., 500.])
@pytest.mark.parametrize('corner', [False, True])
def test_covariance_accuracy(phase, gap, corner):
    # Closely spaced sites in neighbouring boxes exposed the old adapter's
    # covariance error even when its marginal variances were exactly one.
    x = numpy.array([14100., 16000 - gap / 2, 16000 + gap / 2, 17900.])
    y = x.copy() if corner else numpy.full(4, 16000 + 250 * phase)
    sites = locations(x, y - 4_000_000)
    layout = RegularGridLayout((256, 256), (0.25, 0.25), numpy.arange(4),
                               CRS, (-4_000_000., 0.), 0.)
    model = DuNing2021Interpolated()
    continuous = ContinuousDuNing(model)
    local = LocalKrigingFactor.build(
        continuous, IMTS, layout, sites, component=COMPONENT)
    actual = implied_covariance(local, continuous, IMTS)
    actual += numpy.kron(nugget_covariance(model, IMTS), numpy.eye(4))
    rows, columns = layout.grid_coordinates(sites)
    points = numpy.column_stack((rows, columns)) * layout.spacing
    expected = covariance(model, points, IMTS)
    numpy.testing.assert_allclose(numpy.diag(actual), 1, atol=1E-9)
    assert numpy.abs(actual - expected).max() <= 0.01


def test_continuous_grid_covariance():
    model = ContinuousDuNing(DuNing2021Interpolated())
    imts = IMTS[:2]
    factor = CirculantEmbeddingFactor.build(model, imts, (2, 3), 100.)
    basis = factor.apply(numpy.eye(factor.input_size))
    rows, columns = numpy.indices((2, 3))
    points = numpy.column_stack((rows.ravel(), columns.ravel())) * 100
    numpy.testing.assert_allclose(
        basis @ basis.T, covariance(model, points, imts), atol=1E-10)
    layout = RegularGridLayout((2, 3), (100., 100.), numpy.arange(6),
                               CRS, (0., 0.), 0.)
    scalar = ContinuousGridFactor.build(model.model, imts, layout)
    applied = scalar.apply(numpy.eye(scalar.input_size))
    numpy.testing.assert_allclose(
        applied @ applied.T, covariance(model, points, imts), atol=1E-10)


def test_shared_location_and_batches():
    # A coarse grid keeps this factor/application test small. Accuracy at
    # production spacing is covered by the deterministic probes above.
    sites = locations([340000., 370000., 340000.],
                      [340000., 370000., 340000.])
    layout = RegularGridLayout((8, 8), (100., 100.), numpy.arange(3),
                               CRS, (0., 0.), 0.)
    factor = OutputSitesFactor.build(
        DuNing2021Interpolated(), IMTS[:2], sites, layout=layout)
    white = numpy.random.default_rng(8).normal(size=(5, factor.input_size))
    expected = factor.apply(white.T).reshape(2, 3, 5)
    numpy.testing.assert_array_equal(expected[:, 0], expected[:, 2])
    actual = numpy.concatenate(
        [factor.apply(part.T) for part in (white[:2], white[2:])], axis=1)
    numpy.testing.assert_allclose(actual, expected.reshape(6, 5), atol=1E-12)
    assert factor.batch_size(
        factor.nbytes + 3 * factor.workspace_bytes_per_realization) == 3


def test_memory_before_allocation():
    with patch('numpy.fft.rfft2') as allocate:
        with pytest.raises(ValueError, match='workspace bytes'):
            CirculantEmbeddingFactor.build(
                DuNing2021Interpolated(), IMTS, (1_000_000, 1_000_000),
                1., memory_budget=1024)
        allocate.assert_not_called()


def test_nugget_reconstruction():
    model = DuNing2021Interpolated()
    nugget = nugget_covariance(model, IMTS)
    root = covariance_root(nugget)
    numpy.testing.assert_allclose(root @ root.T, nugget, atol=1E-12)
    points = numpy.array([[0., 0.], [0.001, 0.]])
    actual = covariance(ContinuousDuNing(model), points, IMTS)
    actual += numpy.kron(nugget, numpy.eye(2))
    numpy.testing.assert_allclose(actual, covariance(model, points, IMTS))


def test_all_published_imts():
    from openquake.hazardlib.imt import from_string
    from openquake.hazardlib.correlation_models.spatial_cross_imt.\
        du_ning_2021 import _PERIODS
    imts = [from_string(im) for im in
            ['PGA', 'PGV', 'IA', 'CAV', 'RSD575', 'RSD595']]
    imts += [SA(period) for period in _PERIODS] + [SA(0.6)]
    sites = locations([14100., 15999., 16001., 17900.],
                      numpy.full(4, -4_000_000 + 16125.))
    layout = RegularGridLayout((256, 256), (0.25, 0.25), numpy.arange(4),
                               CRS, (-4_000_000., 0.), 0.)
    model = DuNing2021Interpolated()
    continuous = ContinuousDuNing(model)
    local = LocalKrigingFactor.build(
        continuous, imts, layout, sites, component=COMPONENT)
    actual = implied_covariance(local, continuous, imts)
    actual += numpy.kron(nugget_covariance(model, imts), numpy.eye(4))
    rows, columns = layout.grid_coordinates(sites)
    expected = covariance(
        model, numpy.column_stack((rows, columns)) * layout.spacing, imts)
    numpy.testing.assert_allclose(numpy.diag(actual), 1, atol=1E-9)
    assert numpy.abs(actual - expected).max() <= 0.01


def test_conditioned_covariance_accuracy():
    # Conditioning uses the exact station covariance and regression weights.
    # Check the posterior error too, rather than inferring it from the prior.
    sites = locations([14100., 15999., 16001., 17900.],
                      numpy.full(4, -4_000_000 + 16125.))
    layout = RegularGridLayout((256, 256), (0.25, 0.25), numpy.arange(4),
                               CRS, (-4_000_000., 0.), 0.)
    model = DuNing2021Interpolated()
    continuous = ContinuousDuNing(model)
    local = LocalKrigingFactor.build(
        continuous, IMTS, layout, sites, component=COMPONENT)
    approximate = implied_covariance(local, continuous, IMTS)
    approximate += numpy.kron(nugget_covariance(model, IMTS), numpy.eye(4))
    rows, columns = layout.grid_coordinates(sites)
    expected = covariance(
        model, numpy.column_stack((rows, columns)) * layout.spacing, IMTS)
    observed = numpy.concatenate([m * 4 + numpy.array([1, 2])
                                 for m in range(len(IMTS))])
    noise = numpy.eye(len(observed)) * 0.01
    gain = expected[:, observed] @ numpy.linalg.inv(
        expected[numpy.ix_(observed, observed)] + noise)
    transform = numpy.eye(len(expected))
    transform[:, observed] -= gain
    actual = transform @ approximate @ transform.T + gain @ noise @ gain.T
    posterior = expected - gain @ expected[observed]
    assert numpy.abs(actual - posterior).max() <= 0.01


@pytest.mark.parametrize('observed', [1, 4])
def test_joint_conditioning_sampler(observed):
    import pandas
    from openquake.hazardlib.site import SiteCollection
    from openquake.hazardlib.calc.conditioned_gmfs import (
        Input, OutputConditioningSampler, build_station_conditioning,
        build_ce_weights, build_joint_conditioning, _layout_distances,
        StreamedConditioningWeights)
    from openquake.hazardlib.correlation_models.cross_imt.\
        no_cross_correlation import NoCrossCorrelation
    from openquake.hazardlib.tests.calc.conditioned_gmfs_test import BasisRNG
    points = locations([320000., 340000., 370000.],
                       [320000., 340000., 370000.])
    targets = SiteCollection.from_points(points.lons, points.lats)
    stations = targets.filtered([1, 2])
    imts = [PGA(), SA(0.3), SA(0.6), SA(1.)]
    data = pandas.DataFrame({im.string + suffix: numpy.full(2, value)
                             for im in imts for suffix, value in
                             [('_mean', 1.), ('_std', 0.1)]})
    inp = Input(targets, stations, imts, imts[:observed], data,
                DuNing2021Interpolated(), NoCrossCorrelation(), None,
                crs=CRS)
    layout = RegularGridLayout((8, 8), (100., 100.), numpy.empty(0, int),
                               CRS, (0., 0.), 0.)
    target_stats = numpy.zeros((4, 1, 4, 3))
    target_stats[2] = 0.2
    target_stats[3] = 0.8
    station_stats = target_stats[:, :, :observed, [1, 2]]
    DD = _layout_distances(layout, stations, stations)
    station = build_station_conditioning(inp, station_stats, DD)
    sampler = OutputConditioningSampler.build(inp, station, layout, None)
    total = sampler.factor.input_size + 4 + len(station.zeta_D)
    Y, D = sampler.draw_prior(BasisRNG(total), target_stats, station, total)
    weights = build_ce_weights(inp, target_stats, station, sampler, 100000)
    fields = weights.condition(Y, D) - weights.posterior_mean()[:, None]
    YY = _layout_distances(layout, targets, targets)
    YD = _layout_distances(layout, targets, stations)
    reference = build_joint_conditioning(inp, target_stats, station, YY, YD)
    numpy.testing.assert_allclose(
        fields @ fields.T, reference.posterior_covariance(), atol=1E-9)
    streamed = build_ce_weights(
        inp, target_stats, station, sampler, 16, memory_budget=1)
    assert isinstance(streamed, StreamedConditioningWeights)
    numpy.testing.assert_allclose(streamed.posterior_mean(),
                                  weights.posterior_mean(), atol=1E-12)
    numpy.testing.assert_allclose(streamed.condition(Y, D),
                                  weights.condition(Y, D), atol=1E-12)
    rng = numpy.random.default_rng(5)
    one = sampler.draw_prior(rng, target_stats, station, 5)
    rng = numpy.random.default_rng(5)
    first = sampler.draw_prior(rng, target_stats, station, 2)
    last = sampler.draw_prior(rng, target_stats, station, 3)
    for full, a, b in zip(one, first, last):
        numpy.testing.assert_allclose(full, numpy.concatenate((a, b), axis=1))
