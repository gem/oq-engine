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
"""Compatibility imports for cross-IMT ground-motion correlation."""

# DEPRECATION
# -----------
# New code should import cross-IMT models from
# ``openquake.hazardlib.correlation_models.cross_imt``. This module remains
# available during the correlation-framework migration so existing imports,
# job files, and downstream libraries keep working without changed results.
# Remove only after the documented deprecation window and migration of all
# internal callers.

from openquake.hazardlib.correlation_models.base import (
    BetweenEventCrossIMTCorrelationModel as CrossCorrelationBetween,
    CrossIMTCorrelationModel as CrossCorrelation)
from openquake.hazardlib.correlation_models.cross_imt import (
    BakerJayaram2008, Bradley2012, FullCrossCorrelation,
    GodaAtkinson2009, NoCrossCorrelation)

__all__ = [
    'BakerJayaram2008', 'Bradley2012', 'CrossCorrelation',
    'CrossCorrelationBetween', 'FullCrossCorrelation',
    'GodaAtkinson2009', 'NoCrossCorrelation']
