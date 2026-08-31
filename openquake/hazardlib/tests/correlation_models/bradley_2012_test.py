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

from openquake.hazardlib.correlation_models.cross_imt.bradley_2012 import (
    Bradley2012)
from openquake.hazardlib.imt import PGA, PGV, SA


DATA = Path(__file__).with_name('data') / 'BRADLEY_2012'


def test_reference_values():
    reference = numpy.genfromtxt(
        DATA / 'reference.csv', delimiter=',', names=True)
    model = Bradley2012()
    actual = [model.rho(PGV(), SA(row['period'])) for row in reference]
    numpy.testing.assert_allclose(
        actual, reference['correlation'], rtol=1E-12, atol=1E-14)


def test_pgv_pga_correlation():
    assert Bradley2012().rho(PGV(), PGA()) == 0.733


@pytest.mark.parametrize('imts', [
    [PGA(), SA(1.0)],
    [SA(0.3), SA(1.0)],
    [PGV(), SA(0.3), SA(1.0)],
])
def test_rejects_undefined_imt_combinations(imts):
    with pytest.raises(ValueError, match='only a pair containing PGV'):
        Bradley2012().correlation_matrix(imts)


@pytest.mark.parametrize(('imt', 'message'), [
    (SA(0.009), 'periods from 0.01 to 10 s'),
    (SA(10.1), 'periods from 0.01 to 10 s'),
    (SA(1.0, damping=10), 'only 5%-damped SA'),
])
def test_rejects_sa_outside_supported_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        Bradley2012().rho(PGV(), imt)
