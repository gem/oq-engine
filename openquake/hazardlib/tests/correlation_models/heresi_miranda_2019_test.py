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
    heresi_miranda_2019 import HeresiMiranda2019
from openquake.hazardlib.imt import PGA, PGV, SA


DATA = Path(__file__).with_name('data') / 'HERESI_MIRANDA_2019'


def test_reference_values():
    reference = numpy.genfromtxt(
        DATA / 'reference.csv', delimiter=',', names=True)
    model = HeresiMiranda2019()
    actual = []
    for row in reference:
        imt = PGA() if row['period'] == 0 else SA(row['period'])
        matrix = model.correlation_matrix(
            numpy.array([[row['distance']]]), imt)
        actual.append(matrix[0, 0])
    numpy.testing.assert_allclose(
        actual, reference['correlation'], rtol=1E-12, atol=1E-14)


@pytest.mark.parametrize(('imt', 'message'), [
    (PGV(), 'does not support PGV'),
    (SA(10.1), 'periods from 0 to 10 s'),
    (SA(1.0, damping=10), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_supported_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        HeresiMiranda2019().correlation_matrix([[0]], imt)
