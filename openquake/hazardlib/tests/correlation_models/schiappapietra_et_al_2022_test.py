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
from openquake.hazardlib.correlation_models.spatial.\
    schiappapietra_et_al_2022 import (
        SchiappapietraEtAl2022CentralItaly,
        SchiappapietraEtAl2022NorthernItaly,
        SchiappapietraEtAl2022SouthernItaly)
from openquake.hazardlib.imt import PGA, PGV, SA


DATA = (Path(__file__).with_name('data') /
        'SCHIAPPAPIETRA_ET_AL_2022')
MODELS = {
    'northern': SchiappapietraEtAl2022NorthernItaly,
    'central': SchiappapietraEtAl2022CentralItaly,
    'southern': SchiappapietraEtAl2022SouthernItaly,
}


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
    for row in reference:
        period = float(row['period'])
        imt = PGA() if period == 0 else SA(period)
        model = MODELS[row['region']]()
        actual = model.correlation_block(
            numpy.array([[float(row['distance'])]]), [imt], [imt])
        numpy.testing.assert_allclose(
            actual[0, 0], float(row['correlation']),
            rtol=1E-14, atol=1E-15)


def test_regional_classes_are_registered_and_explicit():
    for model_class in MODELS.values():
        assert get_model_class(model_class.name) is model_class
    assert SchiappapietraEtAl2022NorthernItaly.region == 'Northern Italy'
    assert SchiappapietraEtAl2022CentralItaly.region == 'Central Italy'
    assert SchiappapietraEtAl2022SouthernItaly.region == 'Southern Italy'


@pytest.mark.parametrize('model_class', MODELS.values())
def test_covariance_and_factor_are_positive_definite(model_class):
    positions = numpy.array([0.0, 3.0, 17.0, 51.0])
    distances = abs(positions[:, None] - positions)
    sites = Sites(distances)
    model = model_class()
    covariance = model.covariance(sites, [SA(0.5)])

    numpy.testing.assert_allclose(covariance, covariance.T)
    numpy.testing.assert_array_equal(numpy.diag(covariance), 1.0)
    assert numpy.linalg.eigvalsh(covariance).min() > 0
    factor = model.factor(sites, [SA(0.5)], ensure_psd=False)
    numpy.testing.assert_allclose(
        factor.lower_triangle @ factor.lower_triangle.T, covariance)


@pytest.mark.parametrize(('imt', 'message'), [
    (PGV(), 'does not support PGV'),
    (SA(0.09), 'periods from 0.1 to 2 s'),
    (SA(2.01), 'periods from 0.1 to 2 s'),
    (SA(1.0, damping=10.0), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_calibrated_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        SchiappapietraEtAl2022CentralItaly().validate_imts([imt])


def test_rejects_wrong_residual_component():
    with pytest.raises(ValueError, match='provides within correlation'):
        SchiappapietraEtAl2022CentralItaly().correlation_matrix(
            numpy.zeros((1, 1)), PGA(), ResidualComponent.TOTAL)


@pytest.mark.parametrize(('distances', 'message'), [
    (numpy.zeros(2), 'two-dimensional'),
    (numpy.array([[numpy.nan]]), 'finite'),
    (numpy.array([[-1.0]]), 'non-negative'),
])
def test_rejects_invalid_distances(distances, message):
    with pytest.raises(ValueError, match=message):
        SchiappapietraEtAl2022CentralItaly().correlation_matrix(
            distances, PGA())
