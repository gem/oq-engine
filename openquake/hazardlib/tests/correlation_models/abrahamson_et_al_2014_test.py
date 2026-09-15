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
"""Checks against the Abrahamson et al. (2014) supplement.

The reference values were extracted directly from the publisher's electronic
supplement ``esp4bf00365-sup-0001.xls``, available at ``SUPPLEMENT_URL``
below. Neither the OpenQuake implementation nor its production CSV files were
used to compute them.
"""

import csv
from pathlib import Path

import numpy
import pytest

from openquake.hazardlib import const
from openquake.hazardlib.correlation_models.base import ResidualComponent
from openquake.hazardlib.correlation_models.cross_imt.\
    abrahamson_et_al_2014 import (
        AbrahamsonEtAl2014BetweenEvent,
        AbrahamsonEtAl2014WithinEvent,
        _BETWEEN_CORRELATION, _PERIODS, _PUBLISHED_BETWEEN,
        _PUBLISHED_WITHIN)
from openquake.hazardlib.correlation_models.registry import get_model_specs
from openquake.hazardlib.imt import PGA, PGD, PGV, SA, from_string

EPS  = 1e-10
DATA = Path(__file__).with_name('data') / 'ABRAHAMSON_ET_AL_2014'
SUPPLEMENT_URL = (
    'https://onlinelibrary.wiley.com/action/downloadSupplement?'
    'doi=10.1193%2F070913EQS198M&file=esp4bf00365-sup-0001.xls')


def _index(imt):
    if imt.name == 'PGA':
        return 0
    if imt.name == 'PGV':
        return len(_PERIODS) + 1
    return int(numpy.flatnonzero(numpy.isclose(
        _PERIODS, imt.period, rtol=0, atol=EPS))[0]) + 1


def test_supplement_values():
    tables = {
        'within': _PUBLISHED_WITHIN,
        'between': _PUBLISHED_BETWEEN,
    }
    working_tables = {
        'within': _PUBLISHED_WITHIN,
        'between': _BETWEEN_CORRELATION,
    }
    models = {
        'within': AbrahamsonEtAl2014WithinEvent(),
        'between': AbrahamsonEtAl2014BetweenEvent(),
    }
    actual = []
    expected = []
    with (DATA / 'reference.csv').open(
            newline='', encoding='utf8') as reference_file:
        for row in csv.DictReader(reference_file):
            imt1 = from_string(row['imt1'])
            imt2 = from_string(row['imt2'])
            component = row['component']
            actual.append(tables[component][
                _index(imt1), _index(imt2)])
            expected.append(float(row['correlation']))
            assert models[component].rho(imt1, imt2) == pytest.approx(
                working_tables[component][
                    _index(imt1), _index(imt2)], abs=EPS)
    numpy.testing.assert_allclose(actual, expected, rtol=0, atol=0)


def test_between_repair():
    # The published tau table is not PSD. The fixed adjustment is small and
    # produces a positive-definite working correlation matrix.
    raw_eigenvalue = numpy.linalg.eigvalsh(_PUBLISHED_BETWEEN).min()
    eigenvalue = numpy.linalg.eigvalsh(_BETWEEN_CORRELATION).min()
    difference = numpy.abs(
        _BETWEEN_CORRELATION - _PUBLISHED_BETWEEN)
    assert raw_eigenvalue == pytest.approx(
        -0.019717422476525547, abs=EPS)
    assert eigenvalue == pytest.approx(
        9.999951300144685E-6, abs=EPS)
    assert difference.max() == pytest.approx(
        0.003887625919241411, abs=EPS)
    numpy.testing.assert_array_equal(
        _BETWEEN_CORRELATION, _BETWEEN_CORRELATION.T)
    numpy.testing.assert_allclose(
        numpy.diag(_BETWEEN_CORRELATION), 1.0, rtol=0, atol=EPS)


@pytest.mark.parametrize(('model_class', 'expected'), [
    (AbrahamsonEtAl2014WithinEvent, 0.6354359698243993),
    (AbrahamsonEtAl2014BetweenEvent, 0.3927186933456691),
])
def test_interpolation(model_class, expected):
    # SA(0.6) lies between the 0.5 and 0.75 s supplement ordinates.
    model = model_class()
    assert model.rho(PGA(), SA(0.6)) == pytest.approx(
        expected, abs=EPS)
    imts = [PGA(), SA(0.02), SA(0.6), SA(1.0), PGV()]
    matrix = model.correlation_matrix(imts)
    numpy.testing.assert_allclose(matrix, matrix.T, rtol=0, atol=EPS)
    numpy.testing.assert_allclose(
        numpy.diag(matrix), 1.0, rtol=0, atol=EPS)
    assert numpy.linalg.eigvalsh(matrix).min() > 0


def test_metadata():
    specs = get_model_specs('cross_imt')
    between = specs['AbrahamsonEtAl2014BetweenEvent']
    within = specs['AbrahamsonEtAl2014WithinEvent']
    assert between.residual_component is ResidualComponent.BETWEEN_EVENT
    assert within.residual_component is ResidualComponent.WITHIN_EVENT
    for spec in (between, within):
        assert spec.supported_imts == {PGA, PGV, SA}
        assert spec.calibrated_imts == {PGA, PGV, SA}
        assert spec.imc is const.IMC.RotD50
        assert spec.sa_damping == 5.0
        assert spec.sa_period_range == (0.02, 10.0)


@pytest.mark.parametrize(('imt', 'message'), [
    (PGD(), 'does not support PGD'),
    (SA(0.019), 'periods from 0.02 to 10 s'),
    (SA(10.1), 'periods from 0.02 to 10 s'),
    (SA(1.0, damping=10), 'only 5%-damped SA'),
])
def test_domain(imt, message):
    for model in (AbrahamsonEtAl2014BetweenEvent(),
                  AbrahamsonEtAl2014WithinEvent()):
        with pytest.raises(ValueError, match=message):
            model.rho(PGA(), imt)


def test_factor():
    # The factor is only M by M even for a realistic number of sites.
    model = AbrahamsonEtAl2014WithinEvent()
    imts = [PGA(), SA(0.3), SA(0.6), SA(1.0), PGV()]
    factor = model.factor(range(50_000), imts, ensure_psd=False)
    assert factor.lower_triangle.shape == (5, 5)
    assert factor.num_sites == 50_000
