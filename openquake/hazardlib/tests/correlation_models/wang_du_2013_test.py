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

import csv
from pathlib import Path

import numpy
import pytest

from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.registry import get_model_class
from openquake.hazardlib.correlation_models.spatial_cross_imt.\
    wang_du_2013 import (
        WangDu2013PGAIAPGV, WangDu2013SpectralAcceleration)
from openquake.hazardlib.imt import IA, PGA, PGV, SA, from_string


DATA = Path(__file__).with_name('data') / 'WANG_DU_2013'


class Mesh:
    def __init__(self, distances):
        self.distances = distances

    def get_distance_matrix(self):
        return self.distances


class Sites:
    def __init__(self, distances):
        self.mesh = Mesh(distances)


def _reference_rows(filename):
    with (DATA / filename).open(newline='', encoding='utf8') as file:
        return list(csv.DictReader(file))


def _reference_values(model_class, filename):
    actual = []
    expected = []
    imts = []
    for row in _reference_rows(filename):
        imt1 = from_string(row['imt1'])
        imt2 = from_string(row['imt2'])
        model = model_class(float(row['r_vs30']))
        block = model.correlation_block(
            numpy.array([[float(row['distance'])]]), [imt1], [imt2])
        actual.append(block[0, 0])
        expected.append(float(row['rho']))
        imts.append((imt1, imt2))
    return numpy.array(actual), numpy.array(expected), imts


def test_pga_ia_pgv_reference_values():
    actual, expected, _ = _reference_values(
        WangDu2013PGAIAPGV, 'pga_ia_pgv.csv')
    numpy.testing.assert_allclose(
        actual, expected, rtol=1E-13, atol=1E-15)


def test_spectral_acceleration_reference_values():
    actual, expected, imts = _reference_values(
        WangDu2013SpectralAcceleration, 'spectral_acceleration.csv')
    at_endpoint = numpy.array([
        any(imt.period == 10 for imt in pair) for pair in imts])
    numpy.testing.assert_allclose(
        actual[~at_endpoint], expected[~at_endpoint],
        rtol=1E-13, atol=1E-15)
    # The author script uses 10.0001 as its final interpolation node.
    numpy.testing.assert_allclose(
        actual[at_endpoint], expected[at_endpoint],
        rtol=2E-5, atol=1E-14)


def test_models_are_registered_with_calibration_metadata():
    assert get_model_class(
        WangDu2013PGAIAPGV.__name__) is WangDu2013PGAIAPGV
    assert get_model_class(
        WangDu2013SpectralAcceleration.__name__
    ) is WangDu2013SpectralAcceleration
    assert WangDu2013PGAIAPGV.DEFINED_FOR_INTENSITY_MEASURE_TYPES == {
        PGA, IA, PGV}
    assert (
        WangDu2013SpectralAcceleration.DEFINED_FOR_INTENSITY_MEASURE_TYPES
        == {SA})
    assert WangDu2013SpectralAcceleration.DEFINED_FOR_SA_DAMPING == 5.0


@pytest.mark.parametrize(('model', 'imts1', 'imts2'), [
    (WangDu2013PGAIAPGV(), [PGA(), IA()], [IA(), PGV()]),
    (WangDu2013SpectralAcceleration(),
     [SA(0.2), SA(0.75)], [SA(0.3), SA(2.0)]),
])
def test_rectangular_block_uses_imt_major_ordering(model, imts1, imts2):
    distances = numpy.array([[0.0, 10.0, 25.0], [15.0, 5.0, 40.0]])
    correlation = model.correlation_block(distances, imts1, imts2)
    assert correlation.shape == (4, 6)
    for index1, imt1 in enumerate(imts1):
        rows = slice(index1 * 2, (index1 + 1) * 2)
        for index2, imt2 in enumerate(imts2):
            cols = slice(index2 * 3, (index2 + 1) * 3)
            expected = model.correlation_block(
                distances, [imt1], [imt2])
            numpy.testing.assert_allclose(
                correlation[rows, cols], expected)


@pytest.mark.parametrize(('model', 'imts'), [
    (WangDu2013PGAIAPGV(), [PGA(), IA(), PGV()]),
    (WangDu2013SpectralAcceleration(),
     [SA(0.01), SA(0.1), SA(0.3), SA(0.8), SA(2.0), SA(10.0)]),
])
def test_covariance_and_factor_are_positive_definite(model, imts):
    positions = numpy.array([0.0, 3.0, 17.0, 51.0])
    distances = abs(positions[:, None] - positions)
    covariance = model.covariance(Sites(distances), imts)
    assert covariance.dtype == numpy.float64
    numpy.testing.assert_allclose(covariance, covariance.T, atol=1E-15)
    numpy.testing.assert_allclose(numpy.diag(covariance), 1.0)
    assert numpy.linalg.eigvalsh(covariance).min() > 0
    factor = model.factor(Sites(distances), imts, ensure_psd=False)
    numpy.testing.assert_allclose(
        factor.lower_triangle @ factor.lower_triangle.T, covariance)


def test_published_sa_k_matrix_is_symmetric():
    distances = numpy.array([[0.0, 10.0], [20.0, 5.0]])
    model = WangDu2013SpectralAcceleration(25)
    forward = model.correlation_block(
        distances, [SA(0.2)], [SA(2.0)])
    reverse = model.correlation_block(
        distances.T, [SA(2.0)], [SA(0.2)])
    numpy.testing.assert_array_equal(forward, reverse.T)


@pytest.mark.parametrize('value', [-0.1, 25.1, numpy.nan, 'invalid'])
def test_rejects_invalid_vs30_correlation_range(value):
    with pytest.raises(ValueError, match='vs30_correlation_range'):
        WangDu2013PGAIAPGV(value)


def test_default_vs30_correlation_range_is_author_recommendation():
    assert WangDu2013PGAIAPGV().vs30_correlation_range == 12.5
    assert (WangDu2013SpectralAcceleration().vs30_correlation_range ==
            12.5)


@pytest.mark.parametrize(('model', 'imt', 'message'), [
    (WangDu2013PGAIAPGV(), SA(1.0), 'does not support SA'),
    (WangDu2013SpectralAcceleration(), PGA(), 'does not support PGA'),
    (WangDu2013SpectralAcceleration(), SA(0.009),
     'periods from 0.01 to 10 s'),
    (WangDu2013SpectralAcceleration(), SA(10.1),
     'periods from 0.01 to 10 s'),
    (WangDu2013SpectralAcceleration(), SA(1.0, damping=10),
     'only 5%-damped SA'),
])
def test_rejects_imts_outside_calibrated_domain(model, imt, message):
    with pytest.raises(ValueError, match=message):
        model.validate_imts([imt])


@pytest.mark.parametrize(('model', 'imt'), [
    (WangDu2013PGAIAPGV(), PGA()),
    (WangDu2013SpectralAcceleration(), SA(1.0)),
])
def test_rejects_wrong_residual_component(model, imt):
    with pytest.raises(ValueError, match='provides within correlation'):
        model.correlation_block(
            numpy.zeros((1, 1)), [imt],
            component=ResidualComponent.TOTAL)


@pytest.mark.parametrize(('distances', 'message'), [
    (numpy.zeros(2), 'two-dimensional'),
    (numpy.array([[numpy.nan]]), 'finite'),
    (numpy.array([[-1.0]]), 'non-negative'),
])
def test_rejects_invalid_distances(distances, message):
    with pytest.raises(ValueError, match=message):
        WangDu2013SpectralAcceleration().correlation_block(
            distances, [SA(1.0)])
