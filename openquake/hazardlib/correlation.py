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
"""Compatibility imports for spatial ground-motion correlation models."""

# DEPRECATION
# -----------
# New code should import spatial models from
# ``openquake.hazardlib.correlation_models.spatial``. This module remains
# available during the correlation-framework migration so existing imports,
# job files, and downstream libraries keep working without changed results.
# Remove only after the documented deprecation window and migration of all
# internal callers.

from openquake.hazardlib.correlation_models.base import (
    SpatialCorrelationModel as BaseCorrelationModel)
from openquake.hazardlib.correlation_models.spatial.heresi_miranda_2019 import (
    HeresiMiranda2019, _correlation_matrix as hmcorrelation)
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 import (
    JayaramBaker2009, _correlation_matrix as jbcorrelation)


JB2009CorrelationModel = JayaramBaker2009
HM2018CorrelationModel = HeresiMiranda2019

__all__ = [
    'BaseCorrelationModel', 'HM2018CorrelationModel',
    'JB2009CorrelationModel', 'hmcorrelation', 'jbcorrelation']
