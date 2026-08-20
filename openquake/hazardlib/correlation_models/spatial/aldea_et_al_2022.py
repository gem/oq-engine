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

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model


def _distances(sites_or_distances):
    if hasattr(sites_or_distances, 'mesh'):
        distances = sites_or_distances.mesh.get_distance_matrix()
    else:
        distances = sites_or_distances
    distances = numpy.asarray(distances, dtype=float)
    if distances.ndim != 2:
        raise ValueError('Distances must be a two-dimensional array')
    if not numpy.isfinite(distances).all():
        raise ValueError('Distances must be finite')
    if (distances < 0).any():
        raise ValueError('Distances must be non-negative')
    return distances


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
    supported_imts = ('PGA', 'SA')
    imc = 'geometric mean of horizontal components'
    damping = 5.0
    region = 'Chilean subduction zone'

    def validate_imts(self, imts):
        super().validate_imts(imts)
        for imt in imts:
            if imt.name == 'SA':
                if imt.damping != self.damping:
                    raise ValueError(
                        f'{self.name} supports only 5%-damped SA')
                if not 0.1 <= imt.period <= 10.0:
                    raise ValueError(
                        f'{self.name} supports SA periods from 0.1 to 10 s')

    def correlation_matrix(self, sites, imt, component=None, context=None):
        self._get_component(component)
        self.validate_imts([imt])
        period = 0.0 if imt.name == 'PGA' else imt.period
        correlation_range = _correlation_range(period)
        return numpy.exp(-(_distances(sites) / correlation_range) ** 0.59)
