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
"""Abrahamson et al. (2014) residual correlation models.

The authors provide separate cross-IMT correlation matrices for normalized
within-event (``phi``) and between-event (``tau``) residuals in the electronic
supplement. They identify these matrices as inputs for vector hazard and
conditional mean spectra. Both tables cover RotD50 PGA, PGV, and 5%-damped SA
at 22 periods from 0.02 to 10 seconds.

The published between-event table has one negative eigenvalue
(``-0.01972``). It is therefore adjusted once using Higham's alternating
projections with Dykstra correction and a ``1E-5`` eigenvalue floor. No
coefficient changes by more than ``0.00389``. The published within-event
table is already positive definite and remains unchanged.

Intermediate SA periods are supported by linearly interpolating vectors in
correlation space against log period and renormalizing them. This OpenQuake
extension returns the working table exactly at its tabulated periods and
guarantees symmetric, unit-diagonal, positive-semidefinite matrices for
arbitrary periods. Between-event values at tabulated periods include the
small adjustment described above.

References
----------
Abrahamson, N. A., Silva, W. J., and Kamai, R. (2014). Summary of the ASK14
ground motion relation for active crustal regions. Earthquake Spectra, 30(3),
1025-1055. https://doi.org/10.1193/070913EQS198M

Higham, N. J. (2002). Computing the nearest correlation matrix: a problem
from finance. IMA Journal of Numerical Analysis, 22(3), 329-343.
https://doi.org/10.1093/imanum/22.3.329
"""

from pathlib import Path

import numpy

from openquake.hazardlib import const
from openquake.hazardlib.correlation_models.base import (
    CrossIMTCorrelationModel, ResidualComponent,
    TruncatedCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import PGA, PGV, SA


_PERIODS = numpy.array([
    0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5,
    0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0,
], dtype=numpy.float64)
_TABLE_SIZE = len(_PERIODS) + 2
_PGA_INDEX = 0
_PGV_INDEX = _TABLE_SIZE - 1
_DATA = Path(__file__).with_name('data')


def _load_table(filename):
    """Load and validate a published ASK14 correlation table."""
    table = numpy.loadtxt(_DATA / filename, delimiter=',',
                          dtype=numpy.float64)
    if table.shape != (_TABLE_SIZE, _TABLE_SIZE):
        raise ValueError(
            f'Expected a {_TABLE_SIZE} by {_TABLE_SIZE} ASK14 table, got '
            f'{table.shape}')
    if not numpy.array_equal(table, table.T):
        raise ValueError('The ASK14 correlation table must be symmetric')
    if not numpy.array_equal(numpy.diag(table), numpy.ones(_TABLE_SIZE)):
        raise ValueError('The ASK14 correlation table must have unit diagonal')
    table.setflags(write=False)
    return table


def _positive_projection(matrix, floor=1E-5):
    """Return the nearest positive-definite correlation matrix."""
    if numpy.linalg.eigvalsh(matrix).min() >= floor:
        return matrix
    corrected = matrix.copy()
    difference = numpy.zeros_like(matrix)
    for _iteration in range(100):
        adjusted = corrected - difference
        eigenvalues, eigenvectors = numpy.linalg.eigh(adjusted)
        positive = ((eigenvectors * numpy.maximum(eigenvalues, 0)) @
                    eigenvectors.T)
        difference = positive - adjusted
        previous = corrected
        corrected = positive.copy()
        numpy.fill_diagonal(corrected, 1)
        if numpy.linalg.norm(corrected - previous, 'fro') < 1E-14:
            break
    else:
        raise ValueError('ASK14 correlation repair did not converge')

    eigenvalues, eigenvectors = numpy.linalg.eigh(corrected)
    corrected = ((eigenvectors * numpy.maximum(eigenvalues, floor)) @
                 eigenvectors.T)
    scale = numpy.sqrt(numpy.diag(corrected))
    corrected /= scale[:, numpy.newaxis] * scale[numpy.newaxis, :]
    corrected = (corrected + corrected.T) / 2
    numpy.fill_diagonal(corrected, 1)
    corrected.setflags(write=False)
    return corrected


_PUBLISHED_WITHIN = _load_table(
    'abrahamson_et_al_2014_within_event.csv')
_PUBLISHED_BETWEEN = _load_table(
    'abrahamson_et_al_2014_between_event.csv')
_WITHIN_CORRELATION = _positive_projection(_PUBLISHED_WITHIN)
_BETWEEN_CORRELATION = _positive_projection(_PUBLISHED_BETWEEN)


def _weights(imt):
    """Return log-period interpolation weights over the published IMTs."""
    weights = numpy.zeros(_TABLE_SIZE)
    if imt.name == 'PGA':
        weights[_PGA_INDEX] = 1
        return weights
    if imt.name == 'PGV':
        weights[_PGV_INDEX] = 1
        return weights

    upper = int(numpy.searchsorted(_PERIODS, imt.period))
    if upper < len(_PERIODS) and numpy.isclose(
            imt.period, _PERIODS[upper], rtol=0, atol=1E-12):
        weights[upper + 1] = 1
        return weights
    lower = upper - 1
    fraction = numpy.log(imt.period / _PERIODS[lower]) / numpy.log(
        _PERIODS[upper] / _PERIODS[lower])
    weights[lower + 1] = 1 - fraction
    weights[upper + 1] = fraction
    return weights


def _correlations(table, imts1, imts2):
    """Interpolate a PSD cross-correlation block for two IMT lists."""
    weights1 = numpy.array([_weights(imt) for imt in imts1])
    weights2 = numpy.array([_weights(imt) for imt in imts2])
    covariance = weights1 @ table @ weights2.T
    variance1 = numpy.einsum(
        'ij,jk,ik->i', weights1, table, weights1)
    variance2 = numpy.einsum(
        'ij,jk,ik->i', weights2, table, weights2)
    return covariance / numpy.sqrt(
        variance1[:, numpy.newaxis] * variance2[numpy.newaxis, :])


class _AbrahamsonEtAl2014Correlation:
    """Shared ASK14 metadata and correlation-space interpolation."""

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_SA_DAMPING = 5.0
    DEFINED_FOR_SA_PERIOD_RANGE = (0.02, 10.0)
    _CORRELATION = None

    def _rho(self, from_imt, to_imt, context=None):
        return _correlations(
            self._CORRELATION, [from_imt], [to_imt])[0, 0]


@register_model(
    description=('Abrahamson et al. (2014) between-event PGA, PGV, and '
                 'spectral-acceleration correlation'))
class AbrahamsonEtAl2014BetweenEvent(
        _AbrahamsonEtAl2014Correlation,
        TruncatedCrossIMTCorrelationModel):
    """ASK14 between-event cross-IMT correlation.

    The table was derived from ASK14 residuals for active shallow crustal
    earthquakes. The closest application is therefore with the
    :class:`~openquake.hazardlib.gsim.abrahamson_2014.AbrahamsonEtAl2014`
    GMM, although the engine does not restrict its use with other GMMs.
    """

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.BETWEEN_EVENT
    _CORRELATION = _BETWEEN_CORRELATION


@register_model(
    description=('Abrahamson et al. (2014) within-event PGA, PGV, and '
                 'spectral-acceleration correlation'))
class AbrahamsonEtAl2014WithinEvent(
        _AbrahamsonEtAl2014Correlation, CrossIMTCorrelationModel):
    """ASK14 same-site within-event cross-IMT correlation.

    The model correlates IMTs at each site independently. It does not define
    spatial correlation between different sites and therefore does not
    replace a joint spatial-cross-IMT model such as Loth and Baker (2013).
    """

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.WITHIN_EVENT
    _CORRELATION = _WITHIN_CORRELATION
