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
"""Jayaram and Baker (2009) spatial correlation model.

References
----------
Jayaram, N., and Baker, J. W. (2009). Correlation model for spatially
distributed ground-motion intensities. Earthquake Engineering & Structural
Dynamics, 38(15), 1687-1708. https://doi.org/10.1002/eqe.922
"""

import numpy

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import PGA, PGV, SA


def _evaluate_correlation(distances, imt, vs30_clustering=False):
    """Return the Jayaram and Baker (2009) correlation matrix."""
    period = 1.0 if imt.string == 'PGV' else imt.period
    if period < 1:
        if vs30_clustering:
            decay_range = 40.7 - 15.0 * period
        else:
            decay_range = 8.5 + 17.2 * period
    else:
        decay_range = 22.0 + 3.7 * period
    return numpy.exp((-3.0 / decay_range) * distances)


@register_model(
    'JB2009', 'JB2009CorrelationModel',
    description='Jayaram and Baker (2009) spatial correlation')
class JayaramBaker2009(SpatialCorrelationModel):
    """Within-event spatial correlation by Jayaram and Baker (2009).

    The publication calibrated PGA and 5%-damped SA through 10 seconds. PGV
    is retained temporarily using OpenQuake's historical SA(1.0) proxy.
    """

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.WITHIN_EVENT
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    CALIBRATED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}
    INTENSITY_MEASURE_TYPE_APPROXIMATIONS = {PGV: SA(1.0)}
    DEFINED_FOR_SA_DAMPING = 5.0
    DEFINED_FOR_SA_PERIOD_RANGE = (0.01, 10.0)

    def __init__(self, vs30_clustering):
        super().__init__()
        self.vs30_clustering = vs30_clustering

    def _correlation_matrix(self, distances, imt, context=None):
        return _evaluate_correlation(
            distances, imt, self.vs30_clustering)
