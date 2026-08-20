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
"""Markhvida et al. (2018) spatial cross-IMT correlation model.

The principal-component coefficients use the full precision distributed
with the authors' Matlab implementation. Coefficients at intermediate periods
are linearly interpolated in period, as specified by the publication and the
authors' code.

References
----------
Markhvida, M., Ceferino, L., and Baker, J. W. (2018). Modeling spatially
correlated spectral accelerations at multiple periods using principal
component analysis and geostatistics. Earthquake Engineering & Structural
Dynamics, 47(5), 1107-1123. https://doi.org/10.1002/eqe.3007

Author-maintained Matlab implementation
---------------------------------------
https://github.com/bakerjw/Spatial_PCA/tree/9cd0782
"""

import numpy

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model


_PERIODS = numpy.array([
    0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4,
    0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0])

# The first five columns of PCA_coefficients.mat. The five-component model
# is recommended in Section 4.1 of the publication and by the authors' code.
_PCA_COEFFICIENTS = numpy.array([
    [0.27096395624010849,
     -0.13941815711153893,
     0.069042006075982473,
     -0.10609486605905787,
     -0.092288074753640578],
    [0.27018545740937916,
     -0.14173443883719139,
     0.077015668741115859,
     -0.11639353409998979,
     -0.10346437829813765],
    [0.26671648413189297,
     -0.15091802137255739,
     0.1012417504616136,
     -0.14462023036522495,
     -0.12832784505767234],
    [0.25168824045297461,
     -0.18464299884120233,
     0.1788799681008264,
     -0.22132831059711677,
     -0.17555752575312966],
    [0.23643454066026592,
     -0.21892207920247353,
     0.23725418394185016,
     -0.23455903412227364,
     -0.13326708779024415],
    [0.23299464327185404,
     -0.22808798725418472,
     0.23055457291947773,
     -0.16044302411133005,
     0.04005642188723979],
    [0.23891975924445694,
     -0.21190595400306345,
     0.1326462223857624,
     0.082045350292296815,
     0.32794697293788966],
    [0.24724720051341925,
     -0.17405360978451889,
     -0.0082574332781965264,
     0.27738229705779138,
     0.40327133384320257],
    [0.25367709692572277,
     -0.12237588514735337,
     -0.14859558555955846,
     0.36527122315300276,
     0.25318644380567812],
    [0.25492119170750149,
     -0.071319446353372992,
     -0.23703088842126382,
     0.35907310031756512,
     0.040108010656768528],
    [0.25245825421495144,
     0.012509129359153369,
     -0.32712108086481961,
     0.22605319691363626,
     -0.26129762020473013],
    [0.24594424065372994,
     0.079960413980305317,
     -0.35844987281247526,
     0.064099810496083015,
     -0.34179225377939887],
    [0.22575856726405757,
     0.19138103547356652,
     -0.33517630322468533,
     -0.21615263377125335,
     -0.16517895463419158],
    [0.21109716868367367,
     0.25940564980399244,
     -0.2436435848076873,
     -0.32574571881488518,
     0.076348428580887057],
    [0.18838743686086323,
     0.32979974085131442,
     -0.094669261164181881,
     -0.27364637889475724,
     0.35665142635991287],
    [0.17639553310633777,
     0.3573322944208806,
     0.055438750885163209,
     -0.15516195779896869,
     0.35451303508927356],
    [0.16546901834566932,
     0.36004061963727096,
     0.26039217010529109,
     0.066980367208115538,
     0.057270197568061572],
    [0.15958089225685601,
     0.34792715973832439,
     0.34834629520784327,
     0.23939414098469061,
     -0.15721192808252069],
    [0.14883292073049958,
     0.33284769539218007,
     0.36509805168605963,
     0.33122769489470005,
     -0.2813345824566848],
])

# Full-precision values from variogramModel_19PC.mat. Only the first four
# components have short- and long-range structure; the fifth is pure nugget.
_NUGGET = numpy.array([
    2.500000000000001,
    0.5000000000000002,
    0.15000000000000005,
    0.15000000000000005,
    0.31432186713608545,
])
_SHORT_SILL = numpy.array([
    4.520000000000002,
    1.4000000000000004,
    0.4200000000000002,
    0.22500000000000006,
    0.0,
])
_SHORT_RANGE = numpy.array([15.0, 10.0, 15.0, 10.0, 1.0])
_LONG_SILL = numpy.array([
    6.780000000000003,
    2.600000000000001,
    0.6300000000000002,
    0.22500000000000006,
    0.0,
])
_LONG_RANGE = numpy.array([250.0, 160.0, 160.0, 120.0, 1.0])
_SILLS = _NUGGET + _SHORT_SILL + _LONG_SILL

# The authors divide every retained component covariance by the same
# five-component explained-variance factor, 0.9501545851813158. That factor
# cancels when cross-covariance is converted to correlation below.


def _interpolate_coefficients(imts):
    """Linearly interpolate each PCA coefficient at the requested periods."""
    periods = numpy.array([imt.period for imt in imts])
    return numpy.column_stack([
        numpy.interp(periods, _PERIODS, coefficients)
        for coefficients in _PCA_COEFFICIENTS.T
    ])


def _principal_component_covariances(distances):
    """Return the five principal-component covariance blocks."""
    distances = distances[numpy.newaxis, :, :]
    same_site = distances == 0
    short_range = numpy.exp(
        -3 * distances / _SHORT_RANGE[:, numpy.newaxis, numpy.newaxis])
    long_range = numpy.exp(
        -3 * distances / _LONG_RANGE[:, numpy.newaxis, numpy.newaxis])
    return (
        _NUGGET[:, numpy.newaxis, numpy.newaxis] * same_site +
        _SHORT_SILL[:, numpy.newaxis, numpy.newaxis] * short_range +
        _LONG_SILL[:, numpy.newaxis, numpy.newaxis] * long_range)


def _normalized_coefficients(imts):
    coefficients = _interpolate_coefficients(imts)
    variances = (coefficients ** 2) @ _SILLS
    return coefficients / numpy.sqrt(variances[:, numpy.newaxis])


@register_model(
    description='Markhvida et al. (2018) within-event joint correlation')
class MarkhvidaEtAl2018(SpatialCrossIMTCorrelationModel):
    """Within-event spatial cross-IMT model by Markhvida et al. (2018).

    The model uses the recommended first five principal components and was
    calibrated for 5%-damped SA from 0.01 to 5 seconds. The authors do not
    define a PGA proxy, so PGA is not supported.
    """

    name = 'MarkhvidaEtAl2018'
    calibrated_component = ResidualComponent.WITHIN_EVENT
    supported_imts = ('SA',)
    imc = 'RotD50'
    damping = 5.0

    def validate_imts(self, imts):
        super().validate_imts(imts)
        for imt in imts:
            if imt.damping != self.damping:
                raise ValueError(
                    f'{self.name} supports only {self.damping:g}%-damped SA')
            if not 0.01 <= imt.period <= 5.0:
                raise ValueError(
                    f'{self.name} supports SA periods from 0.01 to 5 s, '
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

        coefficients1 = _normalized_coefficients(imts1)
        coefficients2 = _normalized_coefficients(imts2)
        pc_covariances = _principal_component_covariances(distances)
        correlation = numpy.einsum(
            'ik,kab,jk->iajb', coefficients1, pc_covariances,
            coefficients2)
        return correlation.reshape(
            len(imts1) * distances.shape[0],
            len(imts2) * distances.shape[1])
