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
``rhoData.csv`` electronic supplement, SHA-256
``27687e9ae0e4f0f4b9ad1eede3b9d560cd997581a7826975ad9615f50332f77b``.
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


def test_complete_supported_matrix_is_raw_float64():
    imts = [SA(period) for period in _SA_PERIODS]
    imts.extend([PGA(), PGV()])
    matrix = BakerBradley2017().correlation_matrix(imts)
    assert matrix.dtype == numpy.float64
    numpy.testing.assert_array_equal(matrix, matrix.T)
    numpy.testing.assert_array_equal(numpy.diag(matrix), 1)
    assert numpy.linalg.eigvalsh(matrix).min() == pytest.approx(
        -0.0035574748332952884, abs=1E-14)


def test_common_factorization_repairs_indefinite_subset():
    imts = [
        SA(0.042), SA(9.5), SA(0.067), SA(0.42), SA(6.5),
        SA(1.9), SA(9.0), SA(0.08), SA(0.1), SA(1.3), SA(8.0),
        SA(10.0), SA(1.8), SA(0.46), SA(0.025), PGV(),
    ]
    model = BakerBradley2017()
    raw = model.correlation_matrix(imts)
    assert numpy.linalg.eigvalsh(raw).min() < 0
    with pytest.raises(numpy.linalg.LinAlgError):
        model.factor(range(1), imts, ensure_psd=False)
    factor = model.factor(range(1), imts)
    repaired = factor.lower_triangle @ factor.lower_triangle.T
    assert numpy.linalg.eigvalsh(repaired).min() > 0
    numpy.testing.assert_allclose(numpy.diag(repaired), 1)


def test_metadata_and_residual_component():
    model = BakerBradley2017()
    assert model.DEFINED_FOR_RESIDUAL_COMPONENT is ResidualComponent.TOTAL
    assert model.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT is const.IMC.RotD50
    assert model.DEFINED_FOR_INTENSITY_MEASURE_TYPES == {PGA, PGV, SA}
    assert model.rho(
        PGA(), PGV(), ResidualComponent.TOTAL) == pytest.approx(0.67073)
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
