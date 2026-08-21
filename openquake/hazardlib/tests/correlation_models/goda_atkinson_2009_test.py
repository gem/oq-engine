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
    goda_atkinson_2009 import GodaAtkinson2009
from openquake.hazardlib.imt import PGA, PGV, SA


DATA = Path(__file__).with_name('data') / 'GODA_ATKINSON_2009'


def test_reference_values():
    reference = numpy.genfromtxt(
        DATA / 'reference.csv', delimiter=',', names=True)
    model = GodaAtkinson2009()
    actual = [
        model.rho(SA(row['period1']), SA(row['period2']))
        for row in reference]
    numpy.testing.assert_allclose(
        actual, reference['correlation'], rtol=1E-12, atol=1E-14)


def test_pga_preserves_historical_openquake_proxy():
    model = GodaAtkinson2009()
    assert model.rho(PGA(), SA(0.3)) == model._rho(SA(0.05), SA(0.3))


@pytest.mark.parametrize(('imt', 'message'), [
    (PGV(), 'does not support PGV'),
    (SA(0.09), 'periods from 0.1 to 5 s'),
    (SA(5.1), 'periods from 0.1 to 5 s'),
    (SA(1.0, damping=10), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_supported_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        GodaAtkinson2009().rho(SA(1.0), imt)
