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

from pathlib import Path
from types import SimpleNamespace

import numpy
import pytest

from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.spatial_cross_imt.\
    loth_baker_2013 import LothBaker2013
from openquake.hazardlib.imt import PGA, SA


DATA = Path(__file__).with_name('data') / 'LOTH_BAKER_2013'


class Mesh:
    def __init__(self, distances):
        self.distances = distances

    def get_distance_matrix(self):
        return self.distances


def test_reference_values():
    reference = numpy.genfromtxt(
        DATA / 'reference.csv', delimiter=',', names=True)
    model = LothBaker2013()
    actual = []
    for row in reference:
        block = model.correlation_block(
            numpy.array([[row['distance']]]),
            [SA(row['period1'])], [SA(row['period2'])])
        actual.append(block[0, 0])
    numpy.testing.assert_allclose(
        actual, reference['correlation'], rtol=1E-12, atol=1E-14)


def test_rectangular_block_uses_imt_major_ordering():
    model = LothBaker2013()
    distances = numpy.array([
        [0.0, 10.0, 25.0],
        [15.0, 5.0, 40.0],
    ])
    imts1 = [SA(0.15), SA(1.0)]
    imts2 = [SA(0.18), SA(2.0), SA(10.0)]
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


def test_covariance_is_symmetric_positive_definite():
    positions = numpy.array([0.0, 3.0, 17.0, 51.0])
    distances = abs(positions[:, None] - positions)
    sites = SimpleNamespace(mesh=Mesh(distances))
    imts = [SA(period) for period in (
        0.01, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 7.5, 10.0)]
    model = LothBaker2013()

    covariance = model.covariance(sites, imts)
    assert covariance.dtype == numpy.float64
    numpy.testing.assert_allclose(covariance, covariance.T, atol=1E-15)
    numpy.testing.assert_allclose(numpy.diag(covariance), 1.0)
    assert numpy.linalg.eigvalsh(covariance).min() > 0

    factor = model.factor(sites, imts, ensure_psd=False)
    numpy.testing.assert_allclose(
        factor.lower_triangle @ factor.lower_triangle.T,
        covariance, rtol=1E-13, atol=1E-14)


@pytest.mark.parametrize(('imt', 'message'), [
    (PGA(), 'does not support PGA'),
    (SA(0.005), 'periods from 0.01 to 10 s'),
    (SA(10.1), 'periods from 0.01 to 10 s'),
    (SA(1.0, damping=10.0), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_calibrated_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        LothBaker2013().validate_imts([imt])


def test_rejects_wrong_residual_component():
    with pytest.raises(ValueError, match='provides within correlation'):
        LothBaker2013().correlation_block(
            numpy.zeros((1, 1)), [SA(1.0)],
            component=ResidualComponent.TOTAL)


@pytest.mark.parametrize(('distances', 'message'), [
    (numpy.zeros(2), 'two-dimensional'),
    (numpy.array([[numpy.nan]]), 'finite'),
    (numpy.array([[-1.0]]), 'non-negative'),
])
def test_rejects_invalid_distances(distances, message):
    with pytest.raises(ValueError, match=message):
        LothBaker2013().correlation_block(distances, [SA(1.0)])
