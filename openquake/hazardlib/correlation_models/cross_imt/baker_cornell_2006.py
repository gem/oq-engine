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
"""Baker and Cornell (2006) cross-IMT correlation model.

References
----------
Baker, J. W., and Cornell, C. A. (2006). Correlation of response spectral
values for multicomponent ground motions. Bulletin of the Seismological
Society of America, 96(1), 215-227.
https://doi.org/10.1785/0120050060
"""

import math

from openquake.hazardlib.correlation_models.base import (
    CrossIMTCorrelationModel, ResidualComponent)
from openquake.hazardlib.correlation_models.registry import register_model


@register_model(description='Baker and Cornell (2006) SA correlation')
class BakerCornell2006(CrossIMTCorrelationModel):
    """Total-residual spectral correlation by Baker and Cornell (2006)."""

    name = 'BakerCornell2006'
    calibrated_component = ResidualComponent.TOTAL
    # The historical ShakeMap implementation treats PGA and PGV as
    # 0.05-second SA for this correlation calculation.
    supported_imts = ('PGA', 'PGV', 'SA')

    def rho(self, from_imt, to_imt, component=None, context=None):
        self._get_component(component)
        if from_imt == to_imt:
            return 1.0
        min_period = min(from_imt.period or 0.05,
                         to_imt.period or 0.05)
        max_period = max(from_imt.period or 0.05,
                         to_imt.period or 0.05)
        short_period = 1 if min_period < 0.189 else 0
        angle = math.pi / 2 - (
            0.359 + 0.163 * short_period *
            math.log(min_period / 0.189)
        ) * math.log(max_period / min_period)
        return 1 - math.cos(angle)
