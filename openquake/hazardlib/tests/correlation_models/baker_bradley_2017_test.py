# The Hazard Library
# Copyright (C) 2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
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
"""Tests against the corrected Baker-Bradley electronic supplement.

The reference values were extracted directly from the authors' corrected
``rhoDataPD.csv`` electronic supplement, SHA-256
``2ae08d612e6b35ccbe047c7a16428dec25d2f06285d35e7d3eb883c2c9b6821a``.
IM names and row indexes came from the accompanying ``README.csv``. Neither
the OpenQuake implementation nor its production data loader was used to
compute the reference values.
"""

from pathlib import Path

import numpy
import pytest

from openquake.hazardlib import const
from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.cross_imt.baker_bradley_2017 import (
    BakerBradley2017, _SA_PERIODS)
from openquake.hazardlib.imt import IA, PGA, PGV, SA


DATA = Path(__file__).with_name('data') / 'BAKER_BRADLEY_2017'


def _imt(name, period):
    if name == 'PGA':
        return PGA()
    if name == 'PGV':
        return PGV()
    return SA(period)


def test_corrected_author_reference_values():
    reference = numpy.genfromtxt(
        DATA / 'reference.csv', delimiter=',', names=True,
        dtype=None, encoding='ascii')
    model = BakerBradley2017()
    actual = [model.rho(
        _imt(row['imt1'], row['period1']),
        _imt(row['imt2'], row['period2']))
        for row in reference]
    numpy.testing.assert_allclose(
        actual, reference['correlation'], rtol=0, atol=0)


def test_complete_supported_matrix_is_positive_definite_float64():
    imts = [SA(period) for period in _SA_PERIODS]
    imts.extend([PGA(), PGV()])
    matrix = BakerBradley2017().correlation_matrix(imts)
    assert matrix.dtype == numpy.float64
    numpy.testing.assert_array_equal(matrix, matrix.T)
    numpy.testing.assert_array_equal(numpy.diag(matrix), 1)
    assert numpy.linalg.eigvalsh(matrix).min() == pytest.approx(
        1.125427263064056E-5, abs=1E-14)


def test_common_factorization_preserves_author_matrix():
    imts = [
        SA(0.042), SA(9.5), SA(0.067), SA(0.42), SA(6.5),
        SA(1.9), SA(9.0), SA(0.08), SA(0.1), SA(1.3), SA(8.0),
        SA(10.0), SA(1.8), SA(0.46), SA(0.025), PGV(),
    ]
    model = BakerBradley2017()
    expected = model.correlation_matrix(imts)
    factor = model.factor(range(1), imts, ensure_psd=False)
    actual = factor.lower_triangle @ factor.lower_triangle.T
    numpy.testing.assert_allclose(actual, expected, rtol=0, atol=1E-14)


def test_metadata_and_residual_component():
    model = BakerBradley2017()
    assert model.DEFINED_FOR_RESIDUAL_COMPONENT is ResidualComponent.TOTAL
    assert model.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT is const.IMC.RotD50
    assert model.DEFINED_FOR_INTENSITY_MEASURE_TYPES == {PGA, PGV, SA}
    assert model.rho(
        PGA(), PGV(), ResidualComponent.TOTAL) == pytest.approx(0.67070)
    with pytest.raises(ValueError, match='provides total correlation'):
        model.rho(PGA(), PGV(), ResidualComponent.BETWEEN_EVENT)


@pytest.mark.parametrize(('imt', 'message'), [
    (IA(), 'does not support IA'),
    (SA(0.009), 'periods from 0.01 to 10 s'),
    (SA(10.1), 'periods from 0.01 to 10 s'),
    (SA(0.015), 'does not publish a correlation value'),
    (SA(1.0, damping=10), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_published_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        BakerBradley2017().rho(SA(1.0), imt)


def test_accepts_period_boundaries_and_preserves_symmetry():
    model = BakerBradley2017()
    assert model.rho(SA(0.01), SA(0.01)) == 1
    assert model.rho(SA(10.0), SA(10.0)) == 1
    assert model.rho(PGA(), SA(10.0)) == model.rho(SA(10.0), PGA())
