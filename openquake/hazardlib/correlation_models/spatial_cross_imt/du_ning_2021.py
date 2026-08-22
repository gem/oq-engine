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
"""Du and Ning (2021) spatial cross-IMT correlation model.

The equations, principal-component loadings, and nested-covariance
parameters follow the publication's recommended seven-component model.
Matlab functions supplied by Wenqi Du to GEM on 25 May 2022 clarify the
coefficient ordering and the covariance reconstruction. The Matlab code
also interpolates correlations for unlisted SA periods, but that extension
is not described in the paper and can produce a non-unit diagonal. This
implementation therefore supports only the 17 published SA periods.

The calibrated intensity-measure components are not uniform. PGA, PGV, and
SA use the RotD50 component of Campbell and Bozorgnia (2014), whereas IA,
CAV, RSD575, and RSD595 use geometric means of the two as-recorded
horizontal components in their source GMMs. Consequently no single
``DEFINED_FOR_INTENSITY_MEASURE_COMPONENT`` value is declared.

References
----------
Du, W., and Ning, C.-L. (2021). Modeling spatial cross-correlation of
multiple ground motion intensity measures (SAs, PGA, PGV, Ia, CAV, and
significant durations) based on principal component and geostatistical
analyses. Earthquake Spectra, 37(1), 486-504.
https://doi.org/10.1177/8755293020952442

Campbell, K. W., and Bozorgnia, Y. (2014). NGA-West2 ground motion model
for the average horizontal components of PGA, PGV, and 5% damped linear
acceleration response spectra. Earthquake Spectra, 30(3), 1087-1115.

Campbell, K. W., and Bozorgnia, Y. (2019). Ground motion models for the
horizontal components of Arias intensity (AI) and cumulative absolute
velocity (CAV) using the NGA-West2 database. Earthquake Spectra, 35(3),
1289-1310.

Du, W., and Wang, G. (2017). Prediction equations for ground-motion
significant durations using the NGA-West2 database. Bulletin of the
Seismological Society of America, 107(1), 319-333.
"""

import numpy

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import CAV, IA, PGA, PGV, RSD575, RSD595, SA


_PERIODS = numpy.array([
    0.01, 0.05, 0.075, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0,
    3.0, 4.0, 5.0, 7.5, 10.0], dtype=numpy.float64)
_PERIOD_INDEX = {period: index for index, period in enumerate(_PERIODS)}
_OTHER_IMT_INDEX = {
    'PGA': 17,
    'PGV': 18,
    'IA': 19,
    'CAV': 20,
    'RSD575': 21,
    'RSD595': 22,
}

# Table 3, first seven columns. The supplied PC_Coef.mat file uses the same
# values and establishes that rows correspond to IMTs in the order above.
_PCA_COEFFICIENTS = numpy.array([
    [0.28, -0.15, 0.07, 0.04, -0.05, -0.10, -0.08],
    [0.24, -0.19, 0.23, 0.04, -0.18, -0.10, 0.06],
    [0.21, -0.21, 0.29, 0.08, -0.17, 0.06, 0.34],
    [0.20, -0.22, 0.27, 0.08, -0.09, 0.15, 0.45],
    [0.22, -0.20, 0.09, 0.04, 0.23, 0.30, 0.11],
    [0.24, -0.14, -0.11, 0.02, 0.39, 0.28, -0.11],
    [0.24, -0.09, -0.19, -0.05, 0.37, 0.20, -0.13],
    [0.24, -0.04, -0.25, -0.11, 0.31, 0.02, -0.01],
    [0.23, 0.05, -0.30, -0.20, 0.08, -0.19, 0.22],
    [0.22, 0.13, -0.27, -0.27, -0.10, -0.17, 0.32],
    [0.19, 0.22, -0.20, -0.26, -0.23, 0.02, 0.19],
    [0.19, 0.27, -0.10, -0.17, -0.27, 0.20, 0.06],
    [0.17, 0.30, 0.06, -0.00, -0.25, 0.38, -0.20],
    [0.16, 0.32, 0.12, 0.11, -0.11, 0.32, -0.14],
    [0.15, 0.32, 0.15, 0.24, 0.06, 0.17, -0.08],
    [0.12, 0.31, 0.08, 0.37, 0.23, -0.25, 0.16],
    [0.12, 0.30, 0.01, 0.41, 0.20, -0.30, 0.18],
    [0.28, -0.15, 0.07, 0.04, -0.05, -0.10, -0.08],
    [0.26, 0.13, -0.08, 0.09, -0.10, -0.29, -0.23],
    [0.23, -0.12, 0.19, -0.19, -0.10, -0.30, -0.43],
    [0.26, 0.01, 0.25, -0.17, 0.02, -0.19, -0.23],
    [-0.09, 0.21, 0.41, -0.40, 0.29, -0.09, 0.10],
    [-0.07, 0.27, 0.36, -0.38, 0.27, 0.02, 0.09],
], dtype=numpy.float64)

# Table 4. The supplied Func_coeff.mat file confirms the order nugget sill,
# short sill, long sill, short range, and long range.
_NUGGET = numpy.array(
    [1.03, 0.36, 0.13, 0.09, 0.10, 0.11, 0.06],
    dtype=numpy.float64)
_SHORT_SILL = numpy.array(
    [0.88, 1.76, 0.37, 0.26, 0.32, 0.13, 0.16],
    dtype=numpy.float64)
_LONG_SILL = numpy.array(
    [10.11, 2.61, 1.75, 1.11, 0.45, 0.35, 0.25],
    dtype=numpy.float64)
_SHORT_RANGE = numpy.array(
    [15.0, 25.0, 25.0, 20.0, 15.0, 25.0, 25.0],
    dtype=numpy.float64)
_LONG_RANGE = numpy.array(
    [200.0, 150.0, 200.0, 150.0, 150.0, 250.0, 250.0],
    dtype=numpy.float64)
_SILLS = _NUGGET + _SHORT_SILL + _LONG_SILL


def _principal_component_covariances(distances):
    """Return covariance blocks for the seven principal components."""
    distances = distances[numpy.newaxis, :, :]
    same_site = distances == 0
    short_decay = numpy.exp(
        -3 * distances / _SHORT_RANGE[:, numpy.newaxis, numpy.newaxis])
    long_decay = numpy.exp(
        -3 * distances / _LONG_RANGE[:, numpy.newaxis, numpy.newaxis])
    return (
        _NUGGET[:, numpy.newaxis, numpy.newaxis] * same_site +
        _SHORT_SILL[:, numpy.newaxis, numpy.newaxis] * short_decay +
        _LONG_SILL[:, numpy.newaxis, numpy.newaxis] * long_decay)


def _imt_indices(imts):
    """Return rows in the publication's principal-component table."""
    return [
        _PERIOD_INDEX[imt.period]
        if imt.name == 'SA' else _OTHER_IMT_INDEX[imt.name]
        for imt in imts]


def _normalized_coefficients(imts):
    """Return loadings normalized to unit marginal variance."""
    coefficients = _PCA_COEFFICIENTS[_imt_indices(imts)]
    variances = (coefficients ** 2) @ _SILLS
    return coefficients / numpy.sqrt(variances[:, numpy.newaxis])


@register_model(
    description=('Du and Ning (2021) within-event PGA, PGV, IA, CAV, '
                 'duration, and spectral-acceleration joint correlation'))
class DuNing2021(SpatialCrossIMTCorrelationModel):
    """Published seven-PC within-event joint correlation model.

    The 0.9 scale factor in equations 22-24 is common to every
    principal-component covariance and therefore cancels during the
    normalization in equation 12. PGA and SA(0.01) are separate calibrated
    IMTs whose published coefficient rows happen to be identical.
    """

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.WITHIN_EVENT
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {
        SA, PGA, PGV, IA, CAV, RSD575, RSD595}
    DEFINED_FOR_SA_DAMPING = 5.0
    DEFINED_FOR_SA_PERIOD_RANGE = (0.01, 10.0)

    def _validate_imt_combination(self, imts):
        unsupported = sorted({
            imt.period for imt in imts
            if imt.name == 'SA' and imt.period not in _PERIOD_INDEX})
        if unsupported:
            periods = ', '.join(f'{period:g}' for period in _PERIODS)
            requested = ', '.join(f'{period:g}' for period in unsupported)
            raise ValueError(
                f'{self.__class__.__name__} supports only published SA '
                f'periods {periods} s, not {requested} s')

    def _correlation_block(self, distances, imts1, imts2, context=None):
        """Return the joint correlation block in IMT-major order."""
        coefficients1 = _normalized_coefficients(imts1)
        coefficients2 = _normalized_coefficients(imts2)
        pc_covariances = _principal_component_covariances(distances)
        correlation = numpy.einsum(
            'ik,kab,jk->iajb', coefficients1, pc_covariances,
            coefficients2)
        return correlation.reshape(
            len(imts1) * distances.shape[0],
            len(imts2) * distances.shape[1])
