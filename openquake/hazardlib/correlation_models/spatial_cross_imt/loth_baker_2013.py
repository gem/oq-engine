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
"""Loth and Baker (2013) spatial cross-IMT correlation model.

The coefficient tables include the corrections published in the 2020
erratum. The interpolation and full-precision nugget coefficients follow the
authors' reference implementation, updated in 2022.

References
----------
Loth, C., and Baker, J. W. (2013). A spatial cross-correlation model of
spectral accelerations at multiple periods. Earthquake Engineering &
Structural Dynamics, 42(3), 397-417. https://doi.org/10.1002/eqe.2212

Loth, C., and Baker, J. W. (2020). Erratum: A spatial cross-correlation model
for ground motion spectral accelerations at multiple periods. Earthquake
Engineering & Structural Dynamics, 49(3), 315-316.
https://doi.org/10.1002/eqe.3233

Author-maintained Matlab implementation
---------------------------------------
https://github.com/bakerjw/GMMs/blob/master/correlations/lb_2013_spatial_corr.m
"""

import numpy
from scipy.interpolate import griddata

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model


# The final value is the upper interpolation sentinel used by the authors.
# The empirical range of the model ends at 10.0 s.
_PERIODS = numpy.array([
    0.01, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 7.5, 10.0001])

# Corrected short-range coregionalization matrix, B1.
_B1 = numpy.array([
    [0.29, 0.25, 0.23, 0.23, 0.18, 0.10, 0.06, 0.06, 0.06],
    [0.25, 0.30, 0.20, 0.16, 0.10, 0.04, 0.03, 0.04, 0.05],
    [0.23, 0.20, 0.27, 0.18, 0.10, 0.03, 0.00, 0.01, 0.02],
    [0.23, 0.16, 0.18, 0.31, 0.22, 0.14, 0.08, 0.07, 0.07],
    [0.18, 0.10, 0.10, 0.22, 0.33, 0.24, 0.16, 0.13, 0.12],
    [0.10, 0.04, 0.03, 0.14, 0.24, 0.33, 0.26, 0.21, 0.19],
    [0.06, 0.03, 0.00, 0.08, 0.16, 0.26, 0.37, 0.30, 0.26],
    [0.06, 0.04, 0.01, 0.07, 0.13, 0.21, 0.30, 0.28, 0.24],
    [0.06, 0.05, 0.02, 0.07, 0.12, 0.19, 0.26, 0.24, 0.23],
])

# Corrected long-range coregionalization matrix, B2.
_B2 = numpy.array([
    [0.47, 0.40, 0.43, 0.35, 0.27, 0.15, 0.13, 0.09, 0.12],
    [0.40, 0.42, 0.37, 0.25, 0.15, 0.03, 0.04, 0.00, 0.03],
    [0.43, 0.37, 0.45, 0.36, 0.26, 0.15, 0.09, 0.05, 0.08],
    [0.35, 0.25, 0.36, 0.42, 0.37, 0.29, 0.20, 0.16, 0.16],
    [0.27, 0.15, 0.26, 0.37, 0.48, 0.41, 0.26, 0.21, 0.21],
    [0.15, 0.03, 0.15, 0.29, 0.41, 0.55, 0.37, 0.33, 0.32],
    [0.13, 0.04, 0.09, 0.20, 0.26, 0.37, 0.51, 0.49, 0.49],
    [0.09, 0.00, 0.05, 0.16, 0.21, 0.33, 0.49, 0.62, 0.60],
    [0.12, 0.03, 0.08, 0.16, 0.21, 0.32, 0.49, 0.60, 0.68],
])

# Corrected nugget coregionalization matrix, B3. The additional significant
# digits are from the authors' May 2022 update and preserve positive
# definiteness.
_B3 = numpy.array([
    [0.240000000000000, 0.219983028675722, 0.209991239369580,
     0.0899940658151642, -0.0199982490874490, 0.0100004273375877,
     0.0299729607606612, 0.0200291990885140, 0.00995702711846606],
    [0.219983028675722, 0.280000000000000, 0.199999710563431,
     0.0400020556476041, -0.0500003168664929, -5.02841885169300e-7,
     0.0100141900421009, 0.00994747690890486, -0.00996663511790072],
    [0.209991239369580, 0.199999710563431, 0.280000000000000,
     0.0500007637487926, -0.0600002196848805, -1.80663938055364e-7,
     0.0399992445541918, 0.0299487635912810, 0.0100035235224244],
    [0.0899940658151642, 0.0400020556476041, 0.0500007637487926,
     0.270000000000000, 0.139999321454879, 0.0499996979574019,
     0.0499981807238188, 0.0499227563681531, 0.0399858842409999],
    [-0.0199982490874490, -0.0500003168664929, -0.0600002196848805,
     0.139999321454879, 0.190000000000000, 0.0700000354290215,
     0.0499897414826383, 0.0499443288879162, 0.0499652709189241],
    [0.0100004273375877, -5.02841885169300e-7, -1.80663938055364e-7,
     0.0499996979574019, 0.0700000354290215, 0.120000000000000,
     0.0799859494118349, 0.0699172702775962, 0.0599608152312721],
    [0.0299729607606612, 0.0100141900421009, 0.0399992445541918,
     0.0499981807238188, 0.0499897414826383, 0.0799859494118349,
     0.120000000000000, 0.0997643834727755, 0.0800031285024676],
    [0.0200291990885140, 0.00994747690890486, 0.0299487635912810,
     0.0499227563681531, 0.0499443288879162, 0.0699172702775962,
     0.0997643834727755, 0.100000000000000, 0.0896690207890228],
    [0.00995702711846606, -0.00996663511790072, 0.0100035235224244,
     0.0399858842409999, 0.0499652709189241, 0.0599608152312721,
     0.0800031285024676, 0.0896690207890228, 0.0900000000000000],
])
_TABLES = (_B1, _B2, _B3)


def _period_interval(period):
    index = numpy.searchsorted(_PERIODS, period, side='right') - 1
    return min(index, len(_PERIODS) - 2)


def _interpolate_near_diagonal(table, period1, period2, index):
    """Interpolate without flattening the diagonal ridge."""
    low, high = _PERIODS[index:index + 2]
    diagonal = numpy.interp(
        (period1 + period2) / 2, (low, high),
        (table[index, index], table[index + 1, index + 1]))
    return numpy.interp(
        abs(period1 - period2), (0, high - low),
        (diagonal, table[index, index + 1]))


def _interpolate_off_diagonal(table, period1, period2, index1, index2):
    """Apply the authors' local four-point linear interpolation."""
    period1_bounds = _PERIODS[index1:index1 + 2]
    period2_bounds = _PERIODS[index2:index2 + 2]
    grid2, grid1 = numpy.meshgrid(period2_bounds, period1_bounds)
    values = table[index1:index1 + 2, index2:index2 + 2]
    return float(griddata(
        (grid2.ravel(), grid1.ravel()), values.ravel(),
        (period2, period1), method='linear'))


def _interpolate_coefficients(period1, period2):
    index1 = _period_interval(period1)
    index2 = _period_interval(period2)
    if index1 == index2:
        return tuple(_interpolate_near_diagonal(
            table, period1, period2, index1) for table in _TABLES)
    return tuple(_interpolate_off_diagonal(
        table, period1, period2, index1, index2) for table in _TABLES)


@register_model(
    description='Loth and Baker (2013) within-event joint correlation')
class LothBaker2013(SpatialCrossIMTCorrelationModel):
    """Within-event spatial cross-IMT model by Loth and Baker (2013)."""

    name = 'LothBaker2013'
    calibrated_component = ResidualComponent.WITHIN_EVENT
    supported_imts = ('SA',)
    imc = 'Average horizontal'
    damping = 5.0

    def validate_imts(self, imts):
        super().validate_imts(imts)
        for imt in imts:
            if imt.damping != self.damping:
                raise ValueError(
                    f'{self.name} supports only {self.damping:g}%-damped SA')
            if not 0.01 <= imt.period <= 10.0:
                raise ValueError(
                    f'{self.name} supports SA periods from 0.01 to 10 s, '
                    f'not {imt.period:g} s')

    def correlation_block(self, distances, imts1, imts2=None,
                          component=None, context=None):
        """Return the joint correlation block in IMT-major order."""
        self._get_component(component)
        if imts2 is None:
            imts2 = imts1
        self.validate_imts(imts1)
        self.validate_imts(imts2)
        distances = numpy.asarray(distances, dtype=numpy.float64)
        if distances.ndim != 2:
            raise ValueError('Distances must be a two-dimensional matrix')
        if not numpy.all(numpy.isfinite(distances)):
            raise ValueError('Distances must be finite')
        if numpy.any(distances < 0):
            raise ValueError('Distances must be non-negative')

        short_range = numpy.exp(-3 * distances / 20)
        long_range = numpy.exp(-3 * distances / 70)
        same_site = distances == 0
        blocks = []
        for imt1 in imts1:
            row = []
            for imt2 in imts2:
                b1, b2, b3 = _interpolate_coefficients(
                    imt1.period, imt2.period)
                row.append(
                    b1 * short_range + b2 * long_range + b3 * same_site)
            blocks.append(row)
        return numpy.block(blocks)
