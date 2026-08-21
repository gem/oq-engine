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

from openquake.hazardlib import const
from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.registry import get_model_class
from openquake.hazardlib.correlation_models.spatial.aldea_et_al_2022 import (
    AldeaEtAl2022)
from openquake.hazardlib.imt import PGA, PGV, SA


DATA = Path(__file__).with_name('data') / 'ALDEA_ET_AL_2022'


class Mesh:
    def __init__(self, distances):
        self.distances = distances

    def get_distance_matrix(self):
        return self.distances


class Sites:
    def __init__(self, distances):
        self.mesh = Mesh(distances)
        self.size = len(distances)

    def __len__(self):
        return self.size


def test_reference_values():
    with (DATA / 'reference.csv').open(newline='', encoding='utf8') as file:
        reference = list(csv.DictReader(file))
    model = AldeaEtAl2022()
    for row in reference:
        period = float(row['period'])
        imt = PGA() if period == 0 else SA(period)
        actual = model.correlation_block(
            numpy.array([[float(row['distance'])]]), [imt], [imt])
        numpy.testing.assert_allclose(
            actual[0, 0], float(row['correlation']),
            rtol=1E-14, atol=1E-15)


def test_model_is_registered_with_calibration_metadata():
    assert get_model_class(AldeaEtAl2022.__name__) is AldeaEtAl2022
    assert AldeaEtAl2022.DEFINED_FOR_REGION == 'Chilean subduction zone'
    assert AldeaEtAl2022.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT is (
        const.IMC.GEOMETRIC_MEAN)
    assert AldeaEtAl2022.DEFINED_FOR_SA_DAMPING == 5.0


def test_covariance_and_factor_are_positive_definite():
    positions = numpy.array([0.0, 3.0, 17.0, 51.0])
    distances = abs(positions[:, None] - positions)
    sites = Sites(distances)
    model = AldeaEtAl2022()
    covariance = model.covariance(sites, [SA(1.0)])

    numpy.testing.assert_allclose(covariance, covariance.T)
    numpy.testing.assert_array_equal(numpy.diag(covariance), 1.0)
    assert numpy.linalg.eigvalsh(covariance).min() > 0
    factor = model.factor(sites, [SA(1.0)], ensure_psd=False)
    numpy.testing.assert_allclose(
        factor.lower_triangle @ factor.lower_triangle.T, covariance)


@pytest.mark.parametrize(('imt', 'message'), [
    (PGV(), 'does not support PGV'),
    (SA(0.09), 'periods from 0.1 to 10 s'),
    (SA(10.01), 'periods from 0.1 to 10 s'),
    (SA(1.0, damping=10.0), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_calibrated_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        AldeaEtAl2022().validate_imts([imt])


def test_rejects_wrong_residual_component():
    with pytest.raises(ValueError, match='provides within correlation'):
        AldeaEtAl2022().correlation_matrix(
            numpy.zeros((1, 1)), PGA(), ResidualComponent.TOTAL)


@pytest.mark.parametrize(('distances', 'message'), [
    (numpy.zeros(2), 'two-dimensional'),
    (numpy.array([[numpy.nan]]), 'finite'),
    (numpy.array([[-1.0]]), 'non-negative'),
])
def test_rejects_invalid_distances(distances, message):
    with pytest.raises(ValueError, match=message):
        AldeaEtAl2022().correlation_matrix(distances, PGA())
