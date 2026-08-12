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
"""Jayaram and Baker (2009) spatial correlation model."""

import numpy

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model


def jayaram_baker_2009(sites_or_distances, imt,
                       vs30_clustering=False):
    """Return the Jayaram and Baker (2009) correlation matrix."""
    if hasattr(sites_or_distances, 'mesh'):
        distances = sites_or_distances.mesh.get_distance_matrix()
    else:
        distances = sites_or_distances

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
    """Within-event spatial correlation by Jayaram and Baker (2009)."""

    name = 'JayaramBaker2009'
    calibrated_component = ResidualComponent.WITHIN_EVENT
    supported_imts = ('PGA', 'PGV', 'SA')

    def __init__(self, vs30_clustering):
        super().__init__()
        self.vs30_clustering = vs30_clustering

    def correlation_matrix(self, sites, imt, component=None, context=None):
        self._get_component(component)
        return jayaram_baker_2009(
            sites, imt, self.vs30_clustering)
