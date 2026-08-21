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
"""Aldea, Heresi, and Pastén (2022) spatial correlation model.

References
----------
Aldea, S., Heresi, P., and Pastén, C. (2022). Within-event spatial
correlation of peak ground acceleration and spectral pseudo-acceleration
ordinates in the Chilean subduction zone. Earthquake Engineering & Structural
Dynamics, 51(11), 2575-2590. https://doi.org/10.1002/eqe.3674
"""

import numpy

from openquake.hazardlib import const
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import PGA, SA


def _correlation_range(period):
    if period <= 0.4:
        return 14.400 - 17.000 * period
    if period <= 0.75:
        return 14.743 + 7.795 * numpy.log(period)
    if period <= 3.0:
        return 12.500
    return 5.063 + 6.769 * numpy.log(period)


@register_model(
    description=('Aldea, Heresi, and Pastén (2022) Chilean-subduction '
                 'within-event spatial correlation'))
class AldeaEtAl2022(SpatialCorrelationModel):
    """Within-event model for the Chilean subduction zone."""

    name = 'AldeaEtAl2022'
    calibrated_component = ResidualComponent.WITHIN_EVENT
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN
    damping = 5.0
    period_limits = {'SA': (0.1, 10.0)}
    region = 'Chilean subduction zone'

    def _correlation_matrix(self, distances, imt, context=None):
        period = 0.0 if imt.name == 'PGA' else imt.period
        correlation_range = _correlation_range(period)
        return numpy.exp(-(distances / correlation_range) ** 0.59)
