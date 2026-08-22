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
"""Deterministic checks for Du and Ning (2021).

The reference CSV was generated with GNU Octave 8.4.0 from Wenqi Du's
unchanged Matlab functions supplied to GEM on 25 May 2022. The ``du.zip``
SHA-256 is
``35ea324b4783df61f54c6e8ac6ee25d5a7fb9c07abfe857c96d3938c07fde7fe``.
The online Octave runner could not upload binary ``.mat`` files, so their
exact arrays were recreated and checked by element count, sum, sum of
squares, and weighted sum. A separate Python translation of the publication
equations matched the Octave values within 6.1e-16 and did not import OQ.
"""

import csv
from pathlib import Path

import numpy
import pytest

from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.registry import get_model_specs
from openquake.hazardlib.correlation_models.spatial_cross_imt.\
    du_ning_2021 import DuNing2021
from openquake.hazardlib.imt import (
    CAV, IA, PGA, PGD, PGV, RSD575, RSD595, SA, from_string)


DATA = Path(__file__).with_name('data') / 'DU_NING_2021'
PERIODS = (
    0.01, 0.05, 0.075, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0,
    3.0, 4.0, 5.0, 7.5, 10.0)


class Mesh:
    def __init__(self, distances):
        self.distances = distances

    def get_distance_matrix(self):
        return self.distances


class Sites:
    def __init__(self, distances):
        self.mesh = Mesh(distances)


def _all_imts():
    return [SA(period) for period in PERIODS] + [
        PGA(), PGV(), IA(), CAV(), RSD575(), RSD595()]


def test_author_octave_reference_values():
    actual = []
    expected = []
    with (DATA / 'reference.csv').open(
            newline='', encoding='utf8') as reference_file:
        for row in csv.DictReader(reference_file):
            block = DuNing2021().correlation_block(
                numpy.array([[float(row['distance'])]]),
                [from_string(row['imt1'])], [from_string(row['imt2'])])
            actual.append(block[0, 0])
            expected.append(float(row['rho']))
    numpy.testing.assert_allclose(
        actual, expected, rtol=1E-13, atol=1E-15)


def test_registry_and_calibration_metadata():
    spec = get_model_specs('spatial_cross_imt')['DuNing2021']
    assert spec.cls is DuNing2021
    assert spec.residual_component is ResidualComponent.WITHIN_EVENT
    assert spec.supported_imts == {
        SA, PGA, PGV, IA, CAV, RSD575, RSD595}
    assert spec.calibrated_imts == spec.supported_imts
    assert spec.imc is None
    assert spec.sa_damping == 5.0
    assert spec.sa_period_range == (0.01, 10.0)
    assert spec.region is None


def test_rectangular_block_uses_imt_major_ordering():
    distances = numpy.array([
        [0.0, 10.0, 25.0],
        [15.0, 5.0, 40.0],
    ])
    imts1 = [PGA(), SA(1.0)]
    imts2 = [PGV(), CAV(), RSD595()]
    model = DuNing2021()
    correlation = model.correlation_block(distances, imts1, imts2)
    assert correlation.shape == (4, 9)
    for index1, imt1 in enumerate(imts1):
        rows = slice(index1 * 2, (index1 + 1) * 2)
        for index2, imt2 in enumerate(imts2):
            cols = slice(index2 * 3, (index2 + 1) * 3)
            expected = model.correlation_block(
                distances, [imt1], [imt2])
            numpy.testing.assert_allclose(
                correlation[rows, cols], expected)


def test_covariance_and_factor_are_positive_definite():
    positions = numpy.array([0.0, 3.0, 17.0, 51.0])
    distances = abs(positions[:, None] - positions)
    sites = Sites(distances)
    imts = [SA(0.075), SA(0.5), SA(2.0), PGV(), IA(), RSD595()]
    model = DuNing2021()
    covariance = model.covariance(sites, imts)
    assert covariance.dtype == numpy.float64
    numpy.testing.assert_allclose(covariance, covariance.T, atol=1E-15)
    numpy.testing.assert_allclose(numpy.diag(covariance), 1.0)
    assert numpy.linalg.eigvalsh(covariance).min() > 0
    factor = model.factor(sites, imts, ensure_psd=False)
    numpy.testing.assert_allclose(
        factor.lower_triangle @ factor.lower_triangle.T,
        covariance, rtol=1E-13, atol=1E-14)


def test_complete_same_site_matrix_is_positive_semidefinite():
    covariance = DuNing2021().correlation_block(
        numpy.zeros((1, 1)), _all_imts())
    eigenvalues = numpy.linalg.eigvalsh(covariance)
    numpy.testing.assert_allclose(numpy.diag(covariance), 1.0)
    assert eigenvalues.min() > -1E-12
    assert numpy.count_nonzero(eigenvalues > 1E-12) == 7


def test_pair_symmetry():
    distances = numpy.array([[0.0, 10.0], [20.0, 5.0], [50.0, 25.0]])
    model = DuNing2021()
    forward = model.correlation_block(
        distances, [SA(0.1), CAV()], [PGV(), RSD575()])
    reverse = model.correlation_block(
        distances.T, [PGV(), RSD575()], [SA(0.1), CAV()])
    numpy.testing.assert_allclose(forward, reverse.T, atol=1E-15)


def test_zero_and_infinite_distance_limits():
    model = DuNing2021()
    zero = model.correlation_block(
        numpy.zeros((1, 1)), [SA(4.0)], [SA(4.0)])
    distant = model.correlation_block(
        numpy.full((2, 3), 1E6), [SA(4.0), IA()], [PGV()])
    numpy.testing.assert_allclose(zero, 1.0)
    numpy.testing.assert_allclose(distant, 0.0, atol=1E-15)


def test_pga_and_sa_001_are_distinct_but_perfectly_correlated():
    distances = numpy.array([[0.0, 5.0], [20.0, 100.0]])
    model = DuNing2021()
    pga = model.correlation_block(distances, [PGA()], [CAV()])
    sa = model.correlation_block(distances, [SA(0.01)], [CAV()])
    numpy.testing.assert_array_equal(pga, sa)
    combined = model.correlation_block(
        numpy.zeros((1, 1)), [PGA(), SA(0.01)])
    numpy.testing.assert_allclose(combined, numpy.ones((2, 2)))


def test_all_published_sa_periods_are_supported():
    DuNing2021().validate_imts([SA(period) for period in PERIODS])


@pytest.mark.parametrize(('period', 'author_diagonal'), [
    (0.06, 0.982301617604019),
    (0.15, 0.937672330225600),
    (0.6, 0.961149270076905),
    (1.3, 0.974462658605417),
    (8.0, 0.997240559356593),
])
def test_rejects_unpublished_matlab_interpolation(period, author_diagonal):
    assert not numpy.isclose(author_diagonal, 1.0)
    with pytest.raises(ValueError, match='only published SA periods'):
        DuNing2021().validate_imts([SA(period)])


@pytest.mark.parametrize(('imt', 'message'), [
    (PGD(), 'does not support PGD'),
    (SA(0.009), 'periods from 0.01 to 10 s'),
    (SA(10.1), 'periods from 0.01 to 10 s'),
    (SA(10.0, damping=10.0), 'only 5%-damped SA'),
    (SA(10.0001), 'periods from 0.01 to 10 s'),
])
def test_rejects_imts_outside_calibrated_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        DuNing2021().validate_imts([imt])


@pytest.mark.parametrize(
    'component', [ResidualComponent.TOTAL, ResidualComponent.BETWEEN_EVENT])
def test_rejects_wrong_residual_component(component):
    with pytest.raises(ValueError, match='provides within correlation'):
        DuNing2021().correlation_block(
            numpy.zeros((1, 1)), [SA(1.0)], component=component)


@pytest.mark.parametrize(('distances', 'message'), [
    (numpy.zeros(2), 'two-dimensional'),
    (numpy.array([[numpy.nan]]), 'finite'),
    (numpy.array([[-1.0]]), 'non-negative'),
])
def test_rejects_invalid_distances(distances, message):
    with pytest.raises(ValueError, match=message):
        DuNing2021().correlation_block(distances, [SA(1.0)])
