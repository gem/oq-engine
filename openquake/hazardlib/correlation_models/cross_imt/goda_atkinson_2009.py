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
"""Goda and Atkinson (2009) cross-IMT correlation model.

References
----------
Goda, K., and Atkinson, G. M. (2009). Probabilistic characterization of
spatially correlated response spectra for earthquakes in Japan. Bulletin of
the Seismological Society of America, 99(5), 3003-3020.
https://doi.org/10.1785/0120090007
"""

import numpy

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, TruncatedCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import PGA, SA


@register_model(
    'GA2009',
    description='Goda and Atkinson (2009) cross-IMT correlation')
class GodaAtkinson2009(TruncatedCrossIMTCorrelationModel):
    """Between-event cross-IMT correlation by Goda and Atkinson (2009).

    The model was calibrated for 5%-damped SA from 0.1 to 5 seconds. PGA is
    retained temporarily using the engine's historical SA(0.05) proxy, which
    lies outside that calibrated range.
    """

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.BETWEEN_EVENT
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}
    CALIBRATED_FOR_INTENSITY_MEASURE_TYPES = {SA}
    INTENSITY_MEASURE_TYPE_APPROXIMATIONS = {PGA: SA(0.05)}
    DEFINED_FOR_SA_DAMPING = 5.0
    DEFINED_FOR_SA_PERIOD_RANGE = (0.1, 5.0)
    matrix_dtype = numpy.float32

    def _rho(self, from_imt, to_imt, context=None):
        if from_imt == to_imt:
            return 1.0

        period1 = from_imt.period or 0.05
        period2 = to_imt.period or 0.05
        min_period = min(period1, period2)
        max_period = max(period1, period2)
        short_period = 1.0 if min_period < 0.25 else 0.0
        angle = numpy.pi / 2.0 - (
            1.374 + 5.586 * short_period *
            (min_period / max_period) ** 0.728 *
            numpy.log10(min_period / 0.25)
        ) * numpy.log10(max_period / min_period)
        delta = 1.0 + numpy.cos(
            -1.5 * numpy.log10(max_period / min_period))
        correlation = (1.0 - numpy.cos(angle) + delta) / 3.0
        return min(correlation, 1.0)
