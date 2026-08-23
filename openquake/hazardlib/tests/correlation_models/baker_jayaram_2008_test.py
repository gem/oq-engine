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

from openquake.hazardlib.correlation_models.cross_imt.\
    baker_jayaram_2008 import BakerJayaram2008
from openquake.hazardlib.imt import PGA, PGV, SA


DATA = Path(__file__).with_name('data') / 'BAKER_JAYARAM_2008'


def test_reference_values():
    reference = numpy.genfromtxt(
        DATA / 'reference.csv', delimiter=',', names=True)
    model = BakerJayaram2008()
    actual = [
        model.rho(SA(row['period1']), SA(row['period2']))
        for row in reference]
    numpy.testing.assert_allclose(
        actual, reference['correlation'], rtol=1E-12, atol=1E-14)


def test_pga_uses_shortest_calibrated_period():
    model = BakerJayaram2008()
    assert model.rho(PGA(), SA(0.5)) == model.rho(SA(0.01), SA(0.5))


@pytest.mark.parametrize(('imt', 'message'), [
    (PGV(), 'does not support PGV'),
    (SA(0.009), 'periods from 0.01 to 10 s'),
    (SA(10.1), 'periods from 0.01 to 10 s'),
    (SA(1.0, damping=10), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_supported_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        BakerJayaram2008().rho(SA(1.0), imt)
