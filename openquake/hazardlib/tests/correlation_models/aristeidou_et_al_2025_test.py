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
"""Tests against the authors' reference implementation.

The reference values in ``data/ARISTEIDOU_ET_AL_2025/reference.csv`` were
computed with ``aso2024_correlation`` of
https://github.com/Savvinos-Aristeidou/ANN_correlation_models, which reads
the weights from the authors' JSON export of their Keras models. Neither
the OpenQuake implementation nor its HDF5 file was used. The authors'
function was run unchanged except for ``float(x)`` of a ``(1, 1)`` array,
which newer NumPy versions reject and which was replaced by
``float(x.item())``.
"""

import re
from pathlib import Path

import numpy
import pytest

from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.cross_imt.aristeidou_et_al_2025 \
    import AristeidouEtAl2025
from openquake.hazardlib.correlation_models.registry import (
    get_model, get_model_specs)
from openquake.hazardlib.imt import (
    FIV3, IA, PGA, PGV, RSD575, RSD595, SA, Sa_avg2, Sa_avg3)

DATA = Path(__file__).with_name('data') / 'ARISTEIDOU_ET_AL_2025'
FACTORIES = {
    'SA': SA, 'Sa_avg2': Sa_avg2, 'Sa_avg3': Sa_avg3, 'FIV3': FIV3,
    'PGA': PGA, 'PGV': PGV, 'RSD575': RSD575, 'RSD595': RSD595}
EPS = 1E-9


def _imt(name, period):
    if numpy.isnan(period):
        return FACTORIES[name]()
    return FACTORIES[name](float(period))


def _reference():
    return numpy.genfromtxt(
        DATA / 'reference.csv', delimiter=',', names=True,
        dtype=None, encoding='ascii')


def test_reference_values_in_both_orders():
    reference = _reference()
    assert len(reference) == 120
    model = AristeidouEtAl2025()
    direct, swapped = [], []
    for row in reference:
        imt1 = _imt(row['imt1'], row['period1'])
        imt2 = _imt(row['imt2'], row['period2'])
        direct.append(model.rho(imt1, imt2))
        swapped.append(model.rho(imt2, imt1))
    numpy.testing.assert_allclose(
        direct, reference['correlation'], rtol=EPS, atol=EPS)
    numpy.testing.assert_allclose(
        swapped, reference['correlation'], rtol=EPS, atol=EPS)


def test_all_published_pairs_are_covered():
    pairs = {f'{row["imt1"]}-{row["imt2"]}' for row in _reference()}
    names = {'RSD575': 'Ds575', 'RSD595': 'Ds595'}
    pairs = {'-'.join(names.get(n, n) for n in pair.split('-'))
             for pair in pairs}
    assert pairs == set(AristeidouEtAl2025().networks)
    assert len(pairs) == 24


def test_same_imt_is_symmetric_and_unity_on_the_diagonal():
    model = AristeidouEtAl2025()
    for factory in (SA, Sa_avg2, Sa_avg3, FIV3):
        assert model.rho(factory(0.5), factory(0.5)) == 1
        assert model.rho(factory(0.5), factory(2.0)) == model.rho(
            factory(2.0), factory(0.5))


def test_output_is_clipped_to_the_correlation_bounds():
    # the raw ANN output of the pair is 1.0037
    model = AristeidouEtAl2025()
    assert model.rho(Sa_avg3(0.25), Sa_avg3(0.26)) == 1.0
    matrix = model.correlation_matrix([Sa_avg3(0.25), Sa_avg3(0.26)])
    assert numpy.abs(matrix).max() == 1.0


def test_correlation_matrix_and_factorization():
    imts = [SA(0.2), SA(1.0), Sa_avg2(0.5), Sa_avg3(1.0), FIV3(1.0),
            RSD595()]
    model = AristeidouEtAl2025()
    matrix = model.correlation_matrix(imts)
    assert matrix.dtype == numpy.float64
    numpy.testing.assert_array_equal(matrix, matrix.T)
    numpy.testing.assert_array_equal(numpy.diag(matrix), 1)
    assert numpy.linalg.eigvalsh(matrix).min() > 0
    factor = model.factor(range(3), imts, ensure_psd=False)
    lower = factor.lower_triangle
    numpy.testing.assert_allclose(lower @ lower.T, matrix, atol=1E-12)


def test_metadata_and_registry():
    model = get_model('AristeidouEtAl2025', 'cross_imt')
    assert isinstance(model, AristeidouEtAl2025)
    assert model.DEFINED_FOR_RESIDUAL_COMPONENT is ResidualComponent.TOTAL
    assert model.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT is None
    spec = get_model_specs('cross_imt')['AristeidouEtAl2025']
    assert spec.supported_imts == {
        PGA, PGV, RSD575, RSD595, SA, Sa_avg2, Sa_avg3, FIV3}
    assert spec.damping == 5.0
    assert spec.period_range == (0.01, 5.0)
    with pytest.raises(ValueError, match='provides total correlation'):
        model.rho(SA(1.0), FIV3(1.0), ResidualComponent.WITHIN_EVENT)


@pytest.mark.parametrize(('imt1', 'imt2'), [
    (PGA(), PGV()),
    (RSD575(), RSD595()),
    (SA(1.0), PGA()),
    (SA(1.0), PGV()),
])
def test_rejects_pairs_that_are_not_published(imt1, imt2):
    match = re.escape(
        f'does not define a correlation between {imt1.string}')
    with pytest.raises(ValueError, match=match):
        AristeidouEtAl2025().rho(imt1, imt2)


def test_rejects_sets_with_an_undefined_pair():
    with pytest.raises(ValueError, match='does not define a correlation'):
        AristeidouEtAl2025().correlation_matrix([SA(1.0), FIV3(1.0), PGA()])


@pytest.mark.parametrize(('imt', 'message'), [
    (IA(), 'does not support IA'),
    (SA(0.009), 'SA periods from 0.01 to 5 s'),
    (SA(5.1), 'SA periods from 0.01 to 5 s'),
    (FIV3(0.09), 'FIV3 periods from 0.1 to 4 s'),
    (Sa_avg2(4.1), 'Sa_avg2 periods from 0.1 to 4 s'),
    (Sa_avg3(0.05), 'Sa_avg3 periods from 0.1 to 4 s'),
    (SA(1.0, damping=10), 'only 5%-damped SA'),
])
def test_rejects_imts_outside_the_calibrated_domain(imt, message):
    with pytest.raises(ValueError, match=message):
        AristeidouEtAl2025().rho(FIV3(1.0), imt)


def test_accepts_period_boundaries():
    model = AristeidouEtAl2025()
    for imt1, imt2 in [(SA(0.01), FIV3(0.1)), (SA(5.0), FIV3(4.0)),
                       (Sa_avg2(0.1), SA(0.01)), (Sa_avg3(4.0), SA(5.0))]:
        assert -1 <= model.rho(imt1, imt2) <= 1
