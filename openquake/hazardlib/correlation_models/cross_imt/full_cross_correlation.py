# The Hazard Library
# Copyright (C) 2021-2026 GEM Foundation
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
"""Fully correlated cross-IMT residual sampling."""

import numpy

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, TruncatedCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model


@register_model(description='Identical residuals across IMTs')
class FullCrossCorrelation(TruncatedCrossIMTCorrelationModel):
    """Represent perfect cross-IMT correlation."""

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.BETWEEN_EVENT

    def _rho(self, from_imt, to_imt, context=None):
        return 1.0

    def get_inter_eps(self, imts, num_events, rng):
        residuals = self.distribution.rvs(num_events, rng)
        return numpy.array([residuals for imt in imts])
