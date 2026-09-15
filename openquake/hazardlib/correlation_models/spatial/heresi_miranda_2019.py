# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
"""Heresi and Miranda (2019) spatial correlation model.

References
----------
Heresi Venegas, P. C., and Miranda Mijares, E. (2019). Uncertainty in
intraevent spatial correlation of elastic pseudo-acceleration spectral
ordinates. Bulletin of Earthquake Engineering, 17(3), 1099-1115.
https://doi.org/10.1007/s10518-018-0506-6
"""

import numpy

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import PGA, SA


def _evaluate_correlation(distances, imt, uncertainty_multiplier=0):
    """Return the Heresi and Miranda (2019) correlation matrix."""
    period = imt.period
    if period < 1.37:
        median_beta = 4.231 * period ** 2 - 5.180 * period + 13.392
    else:
        median_beta = 0.140 * period ** 2 - 2.249 * period + 17.050
    stddev_beta = 4.63E-3 * period ** 2 + 0.028 * period + 0.713
    if uncertainty_multiplier:
        beta = numpy.random.lognormal(
            numpy.log(median_beta), stddev_beta * uncertainty_multiplier)
    else:
        beta = median_beta
    return numpy.exp(-numpy.power(distances / beta, 0.55))


@register_model(
    'HM2019', 'HM2018', 'HM2018CorrelationModel',
    description='Heresi and Miranda (2019) spatial correlation')
class HeresiMiranda2019(SpatialCorrelationModel):
    """Within-event spatial correlation by Heresi and Miranda (2019)."""

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.WITHIN_EVENT
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}
    DEFINED_FOR_SA_DAMPING = 5.0
    DEFINED_FOR_SA_PERIOD_RANGE = (0.0, 10.0)

    def __init__(self, uncertainty_multiplier=0):
        super().__init__()
        self.uncertainty_multiplier = uncertainty_multiplier
        self.distance_matrix = {}

    def _correlation_matrix(self, distances, imt, context=None):
        return _evaluate_correlation(
            distances, imt, self.uncertainty_multiplier)

    def apply_correlation(self, sites, imt, residuals, stddev_intra):
        num_sites = len(sites)
        assert len(residuals) == len(stddev_intra) == num_sites
        stddev_matrix = numpy.diag(stddev_intra)
        if self.uncertainty_multiplier == 0:
            normalized = residuals / stddev_intra[:, None]
            covariance = (stddev_matrix @
                          self.correlation_matrix(sites, imt) @
                          stddev_matrix)
            return numpy.linalg.cholesky(covariance) @ normalized

        correlated = numpy.zeros_like(residuals)
        for sample in range(residuals.shape[1]):
            correlation = self.correlation_matrix(sites, imt)
            covariance = stddev_matrix @ correlation @ stddev_matrix
            correlated[:, sample] = numpy.random.multivariate_normal(
                numpy.zeros(num_sites), covariance, 1)
        return correlated
