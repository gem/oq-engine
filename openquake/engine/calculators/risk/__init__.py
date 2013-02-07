# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""Information about the calculators available for the Risk engine."""

from __future__ import absolute_import

from .classical.core import ClassicalRiskCalculator
from .classical_bcr.core import ClassicalBCRRiskCalculator
from .event_based.core import EventBasedRiskCalculator
from .event_based_bcr.core import EventBasedBCRRiskCalculator
from .scenario.core import ScenarioRiskCalculator
from .scenario_damage.core import ScenarioDamageRiskCalculator

CALCULATORS = {
    'classical': ClassicalRiskCalculator,
    'classical_bcr': ClassicalBCRRiskCalculator,
    'event_based': EventBasedRiskCalculator,
    'event_based_bcr': EventBasedBCRRiskCalculator,
    'scenario': ScenarioRiskCalculator,
    'scenario_damage': ScenarioDamageRiskCalculator,
}
