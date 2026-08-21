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
"""Schiappapietra et al. (2022) spatial correlation models.

References
----------
Schiappapietra, E., Stripajová, S., Pažák, P., Douglas, J., and
Trendafiloski, G. (2022). Exploring the impact of spatial correlations of
earthquake ground motions in the catastrophe modelling process: a case study
for Italy. Bulletin of Earthquake Engineering, 20, 5747-5773.
https://doi.org/10.1007/s10518-022-01413-z
"""

import numpy

from openquake.hazardlib import const
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import PGA, SA


class _SchiappapietraEtAl2022(SpatialCorrelationModel):
    """Common implementation for the three regional models.

    The paper also provides the event-to-event dispersion of the correlation
    range. This implementation returns the deterministic median model. It does
    not sample the published dispersion inside matrix evaluation, which would
    make results dependent on call order and incompatible with factor caching.
    """

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.WITHIN_EVENT
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_SA_DAMPING = 5.0
    DEFINED_FOR_SA_PERIOD_RANGE = (0.1, 2.0)
    DEFINED_FOR_REGION = None
    range_coefficients = None

    def _range(self, period):
        a0, a1, a2, hinge = self.range_coefficients
        if hinge is None:
            return a0 + a1 * period
        slope = a1 if period <= hinge else a2
        return a0 + slope * (period - hinge)

    def _correlation_matrix(self, distances, imt, context=None):
        period = 0.0 if imt.name == 'PGA' else imt.period
        return numpy.exp(-3.0 * distances / self._range(period))


@register_model(
    description=('Schiappapietra et al. (2022) Northern Italy '
                 'within-event spatial correlation'))
class SchiappapietraEtAl2022NorthernItaly(_SchiappapietraEtAl2022):
    """Median model calibrated for Northern Italy."""

    DEFINED_FOR_REGION = 'Northern Italy'
    range_coefficients = (27.48, -52.20, 15.81, 0.55)


@register_model(
    description=('Schiappapietra et al. (2022) Central Italy '
                 'within-event spatial correlation'))
class SchiappapietraEtAl2022CentralItaly(_SchiappapietraEtAl2022):
    """Median model calibrated for Central Italy."""

    DEFINED_FOR_REGION = 'Central Italy'
    range_coefficients = (17.87, -8.52, 7.85, 1.0)


@register_model(
    description=('Schiappapietra et al. (2022) Southern Italy '
                 'within-event spatial correlation'))
class SchiappapietraEtAl2022SouthernItaly(_SchiappapietraEtAl2022):
    """Median model calibrated for Southern Italy.

    The publication notes that this regional model is less well constrained
    than the Northern and Central Italy models because only six earthquakes
    were available for its calibration.
    """

    DEFINED_FOR_REGION = 'Southern Italy'
    range_coefficients = (23.25, -5.44, None, None)
