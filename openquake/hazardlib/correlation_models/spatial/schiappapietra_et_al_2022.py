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


class _SchiappapietraEtAl2022(SpatialCorrelationModel):
    """Common implementation for the three regional models.

    The paper also provides the event-to-event dispersion of the correlation
    range. This implementation returns the deterministic median model. It does
    not sample the published dispersion inside matrix evaluation, which would
    make results dependent on call order and incompatible with factor caching.
    """

    calibrated_component = ResidualComponent.WITHIN_EVENT
    supported_imts = ('PGA', 'SA')
    imc = 'RotD50'
    damping = 5.0
    region = None
    range_coefficients = None

    def validate_imts(self, imts):
        super().validate_imts(imts)
        for imt in imts:
            if imt.name == 'SA':
                if imt.damping != self.damping:
                    raise ValueError(
                        f'{self.name} supports only 5%-damped SA')
                if not 0.1 <= imt.period <= 2.0:
                    raise ValueError(
                        f'{self.name} supports SA periods from 0.1 to 2 s')

    def _range(self, period):
        a0, a1, a2, hinge = self.range_coefficients
        if hinge is None:
            return a0 + a1 * period
        slope = a1 if period <= hinge else a2
        return a0 + slope * (period - hinge)

    def correlation_matrix(self, sites, imt, component=None, context=None):
        self._get_component(component)
        self.validate_imts([imt])
        period = 0.0 if imt.name == 'PGA' else imt.period
        return numpy.exp(-3.0 * _distances(sites) / self._range(period))


@register_model(
    description=('Schiappapietra et al. (2022) Northern Italy '
                 'within-event spatial correlation'))
class SchiappapietraEtAl2022NorthernItaly(_SchiappapietraEtAl2022):
    """Median model calibrated for Northern Italy."""

    name = 'SchiappapietraEtAl2022NorthernItaly'
    region = 'Northern Italy'
    range_coefficients = (27.48, -52.20, 15.81, 0.55)


@register_model(
    description=('Schiappapietra et al. (2022) Central Italy '
                 'within-event spatial correlation'))
class SchiappapietraEtAl2022CentralItaly(_SchiappapietraEtAl2022):
    """Median model calibrated for Central Italy."""

    name = 'SchiappapietraEtAl2022CentralItaly'
    region = 'Central Italy'
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

    name = 'SchiappapietraEtAl2022SouthernItaly'
    region = 'Southern Italy'
    range_coefficients = (23.25, -5.44, None, None)
