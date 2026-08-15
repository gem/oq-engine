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
"""Baker and Jayaram (2008) cross-IMT correlation model.

References
----------
Baker, J. W., and Jayaram, N. (2008). Correlation of Spectral Acceleration
Values from NGA Ground Motion Models. Earthquake Spectra, 24(1), 299-317.
https://doi.org/10.1193/1.2857544
"""

import numpy
from scipy import constants

from openquake.hazardlib.correlation_models.base import (
    CrossIMTCorrelationModel, ResidualComponent)
from openquake.hazardlib.correlation_models.registry import register_model


@register_model(
    'BJ2008',
    description='Baker and Jayaram (2008) cross-IMT correlation')
class BakerJayaram2008(CrossIMTCorrelationModel):
    """Total-residual cross-IMT correlation for GMRotI50."""

    name = 'BakerJayaram2008'
    calibrated_component = ResidualComponent.TOTAL
    supported_imts = ('PGA', 'SA')
    imc = 'GMRotI50'

    def rho(self, from_imt, to_imt, component=None, context=None):
        self._get_component(component)
        from_period = from_imt.period
        to_period = to_imt.period
        if numpy.abs(from_period - to_period) < 1E-10:
            return 1.0

        min_period = min(from_period, to_period)
        max_period = max(from_period, to_period)
        c1 = 1 - numpy.cos(
            constants.pi / 2 - 0.366 * numpy.log(
                max_period / max(min_period, 0.109)))
        c2 = 0.0
        if max_period < 0.2:
            term1 = 1.0 - 1.0 / (
                1.0 + numpy.exp(100.0 * max_period - 5.0))
            term2 = ((max_period - min_period) /
                     (max_period - 0.0099))
            c2 = 1 - 0.105 * term1 * term2
        c3 = c2 if max_period < 0.109 else c1
        c4 = c1 + 0.5 * (numpy.sqrt(c3) - c3) * (
            1 + numpy.cos(constants.pi * min_period / 0.109))
        if max_period < 0.109:
            return c2
        if min_period > 0.109:
            return c1
        if max_period < 0.2:
            return min(c2, c4)
        return c4
