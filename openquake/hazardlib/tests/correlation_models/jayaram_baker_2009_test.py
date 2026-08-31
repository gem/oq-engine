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

import numpy
import pytest

from openquake.hazardlib.correlation_models.spatial.\
    jayaram_baker_2009 import JayaramBaker2009
from openquake.hazardlib.imt import PGV, SA


DATA = Path(__file__).with_name('data') / 'JAYARAM_BAKER_2009'


def test_reference_values():
    reference = numpy.genfromtxt(
        DATA / 'reference.csv', delimiter=',', names=True)
    actual = []
    for row in reference:
        model = JayaramBaker2009(bool(row['vs30_clustering']))
        matrix = model.correlation_matrix(
            numpy.array([[row['distance']]]), SA(row['period']))
        actual.append(matrix[0, 0])
    numpy.testing.assert_allclose(
        actual, reference['correlation'], rtol=1E-12, atol=1E-14)


def test_pgv_preserves_historical_openquake_proxy():
    distances = numpy.array([[0.0, 10.0], [10.0, 0.0]])
    model = JayaramBaker2009(False)
    numpy.testing.assert_array_equal(
        model.correlation_matrix(distances, PGV()),
        model.correlation_matrix(distances, SA(1.0)))


@pytest.mark.parametrize(('imt', 'message'), [
    (SA(0.009), 'periods from 0.01 to 10 s'),
    (SA(10.1), 'periods from 0.01 to 10 s'),
    (SA(1.0, damping=10), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_supported_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        JayaramBaker2009(False).correlation_matrix([[0]], imt)
