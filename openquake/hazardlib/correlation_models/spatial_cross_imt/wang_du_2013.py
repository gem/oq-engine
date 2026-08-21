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
"""Wang and Du (2013) spatial cross-IMT correlation models.

References
----------
Wang, G., and Du, W. (2013). Spatial cross-correlation models for vector
intensity measures (PGA, Ia, PGV, and SAs) considering regional site
conditions. Bulletin of the Seismological Society of America, 103(6),
3189-3204. https://doi.org/10.1785/0120130061

The implementation follows the published equations and coefficient tables.
Matlab functions supplied by Wenqi Du to GEM on 25 May 2022 were used
independently to generate the test reference values.
"""

import numpy

from openquake.hazardlib import const
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import IA, PGA, PGV, SA


_DEFAULT_VS30_CORRELATION_RANGE = 12.5
_MAX_VS30_CORRELATION_RANGE = 25.0

_PGA_IA_PGV_INDEX = {'PGA': 0, 'IA': 1, 'PGV': 2}
_P0 = numpy.array([
    [1.00, 0.91, 0.65],
    [0.91, 1.00, 0.71],
    [0.65, 0.71, 1.00],
])
_K = numpy.array([
    [0.28, 0.24, 0.17],
    [0.24, 0.22, 0.16],
    [0.17, 0.16, 0.31],
])

_PERIODS = numpy.array([0.01, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 7.5, 10.0])
_P01_SA = numpy.array([
    [0.96, 0.90, 0.80, 0.50, 0.15, 0.09, 0.10, 0.09, 0.04],
    [0.90, 0.96, 0.81, 0.36, 0.08, 0.04, 0.05, 0.05, 0.02],
    [0.80, 0.81, 0.93, 0.44, 0.10, 0.05, 0.09, 0.08, 0.05],
    [0.50, 0.36, 0.44, 0.76, 0.25, 0.17, 0.14, 0.13, 0.07],
    [0.15, 0.08, 0.10, 0.25, 0.62, 0.45, 0.34, 0.37, 0.31],
    [0.09, 0.04, 0.05, 0.17, 0.45, 0.54, 0.42, 0.42, 0.35],
    [0.10, 0.05, 0.09, 0.14, 0.34, 0.42, 0.47, 0.46, 0.39],
    [0.09, 0.05, 0.08, 0.13, 0.37, 0.42, 0.46, 0.57, 0.40],
    [0.04, 0.02, 0.05, 0.07, 0.31, 0.35, 0.39, 0.40, 0.56],
])
_P02_SA = numpy.array([
    [0.04, 0.00, 0.01, 0.04, 0.08, 0.02, 0.02, 0.00, 0.02],
    [0.00, 0.04, 0.01, 0.00, 0.01, 0.00, 0.00, 0.00, 0.00],
    [0.01, 0.01, 0.07, 0.08, 0.08, 0.01, 0.00, 0.00, 0.00],
    [0.04, 0.00, 0.08, 0.24, 0.28, 0.20, 0.15, 0.13, 0.13],
    [0.08, 0.01, 0.08, 0.28, 0.38, 0.22, 0.23, 0.18, 0.19],
    [0.02, 0.00, 0.01, 0.20, 0.22, 0.46, 0.32, 0.25, 0.25],
    [0.02, 0.00, 0.00, 0.15, 0.23, 0.32, 0.53, 0.43, 0.42],
    [0.00, 0.00, 0.00, 0.13, 0.18, 0.25, 0.43, 0.43, 0.41],
    [0.02, 0.00, 0.00, 0.13, 0.19, 0.25, 0.42, 0.41, 0.44],
])
_K_SA = numpy.array([
    [0.28, 0.26, 0.20, 0.13, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.26, 0.27, 0.21, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.20, 0.21, 0.20, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.13, 0.10, 0.10, 0.11, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.14, 0.11, 0.08, 0.10, 0.10],
    [0.00, 0.00, 0.00, 0.00, 0.11, 0.11, 0.09, 0.11, 0.12],
    [0.00, 0.00, 0.00, 0.00, 0.08, 0.09, 0.11, 0.12, 0.12],
    [0.00, 0.00, 0.00, 0.00, 0.10, 0.11, 0.12, 0.14, 0.13],
    [0.00, 0.00, 0.00, 0.00, 0.10, 0.12, 0.12, 0.13, 0.17],
])


def _interpolate(table, period1, period2):
    """Bilinearly interpolate a coregionalization table in period."""
    rows = numpy.array([
        numpy.interp(period2, _PERIODS, row) for row in table])
    return numpy.interp(period1, _PERIODS, rows)


def _coefficient_matrix(table, periods1, periods2):
    return numpy.array([
        [_interpolate(table, period1, period2) for period2 in periods2]
        for period1 in periods1
    ])


class _WangDu2013(SpatialCrossIMTCorrelationModel):
    """Shared parameter and input validation for both publication models."""

    calibrated_component = ResidualComponent.WITHIN_EVENT
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    def __init__(self,
                 vs30_correlation_range=_DEFAULT_VS30_CORRELATION_RANGE):
        try:
            self.vs30_correlation_range = float(vs30_correlation_range)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                'vs30_correlation_range must be a number in km') from exc
        self.validate()

    def validate(self):
        super().validate()
        value = self.vs30_correlation_range
        if not numpy.isfinite(value) or not 0 <= value <= 25:
            raise ValueError(
                'vs30_correlation_range must be between 0 and 25 km')

    def _assemble(self, distances, p01, p02, k, long_range):
        short_decay = numpy.exp(-3 * distances / 10)
        long_decay = numpy.exp(-3 * distances / long_range)
        site_adjustment = (
            self.vs30_correlation_range / 10 *
            (long_decay - short_decay))
        correlation = (
            p01[:, None, :, None] * short_decay[None, :, None, :] +
            p02[:, None, :, None] * long_decay[None, :, None, :] +
            k[:, None, :, None] * site_adjustment[None, :, None, :])
        return correlation.reshape(
            len(p01) * distances.shape[0],
            p01.shape[1] * distances.shape[1])


@register_model(
    description=('Wang and Du (2013) within-event PGA, IA, and PGV '
                 'joint correlation'))
class WangDu2013PGAIAPGV(_WangDu2013):
    """Joint correlation for the publication's PGA, IA, and PGV set."""

    name = 'WangDu2013PGAIAPGV'
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, IA, PGV}

    def _correlation_block(self, distances, imts1, imts2, context=None):
        """Return the joint correlation block in IMT-major order."""
        indices1 = [_PGA_IA_PGV_INDEX[imt.name] for imt in imts1]
        indices2 = [_PGA_IA_PGV_INDEX[imt.name] for imt in imts2]
        p0 = _P0[numpy.ix_(indices1, indices2)]
        k = _K[numpy.ix_(indices1, indices2)]
        return self._assemble(
            distances, p0, numpy.zeros_like(p0), k, 60)


@register_model(
    description=('Wang and Du (2013) within-event spectral-acceleration '
                 'joint correlation'))
class WangDu2013SpectralAcceleration(_WangDu2013):
    """Joint correlation for 5%-damped SA from 0.01 to 10 seconds.

    The publication permits linear interpolation of the tabulated
    coregionalization matrices. Interpolation can change their marginal
    variances, so the resulting covariance is normalized to a correlation
    matrix. This preserves the standard deviations supplied by the GSIM.
    """

    name = 'WangDu2013SpectralAcceleration'
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {SA}
    damping = 5.0
    period_limits = {'SA': (0.01, 10.0)}

    def _correlation_block(self, distances, imts1, imts2, context=None):
        """Return the normalized joint correlation block."""
        periods1 = numpy.array([imt.period for imt in imts1])
        periods2 = numpy.array([imt.period for imt in imts2])
        p01 = _coefficient_matrix(_P01_SA, periods1, periods2)
        p02 = _coefficient_matrix(_P02_SA, periods1, periods2)
        k = _coefficient_matrix(_K_SA, periods1, periods2)
        variance1 = numpy.array([
            _interpolate(_P01_SA + _P02_SA, period, period)
            for period in periods1])
        variance2 = numpy.array([
            _interpolate(_P01_SA + _P02_SA, period, period)
            for period in periods2])
        normalization = numpy.sqrt(variance1[:, None] * variance2)
        return self._assemble(
            distances, p01 / normalization, p02 / normalization,
            k / normalization, 70)
