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
"""Bradley (2012) cross-IMT correlation model.

References
----------
Bradley, B. A. (2012). Empirical correlations between peak ground velocity
and spectrum-based intensity measures. Earthquake Spectra, 28(1), 17-35.
https://doi.org/10.1193/1.3675582
"""

import numpy

from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, TruncatedCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model


@register_model(description='Bradley (2012) PGV and spectrum correlation')
class Bradley2012(TruncatedCrossIMTCorrelationModel):
    """Total-residual correlation between PGV and spectrum-based IMTs."""

    name = 'Bradley2012'
    calibrated_component = ResidualComponent.TOTAL
    supported_imts = ('PGV', 'PGA', 'SA')

    def rho(self, from_imt, to_imt, component=None, context=None):
        self._get_component(component)
        if from_imt == to_imt:
            return 1
        if from_imt.string != 'PGV' and to_imt.string != 'PGV':
            return 0
        period = (to_imt.period if from_imt.string == 'PGV'
                  else from_imt.period)
        if period < 0.01:
            return 0.733
        if period < 0.1:
            a, b, c, d = 0.73, 0.54, 0.045, 1.8
        elif period < 0.75:
            a, b, c, d = 0.54, 0.81, 0.28, 1.5
        elif period < 2.5:
            a, b, c, d = 0.80, 0.76, 1.1, 3.0
        else:
            a, b, c, d = 0.76, 0.70, 5.0, 3.2
        return ((a + b) / 2 -
                (a - b) / 2 * numpy.tanh(d * numpy.log(period / c)))
