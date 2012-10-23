# Copyright (c) 2010-2012, GEM Foundation.
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

"""This package contains Hazard calculator classes and utilities."""


from openquake.calculators.hazard.disagg.core import DisaggHazardCalculator
from openquake.calculators.hazard.scenario.core import ScenarioHazardCalculator
from openquake.calculators.hazard.uhs.core import UHSCalculator

from openquake.calculators.hazard.classical.core import (
    ClassicalHazardCalculator)
from openquake.calculators.hazard.event_based.core_next import (
    EventBasedHazardCalculator)


CALCULATORS = {
    'event_based': EventBasedHazardCalculator,
    'event_based_bcr': EventBasedHazardCalculator,
    'disaggregation': DisaggHazardCalculator,
    'scenario': ScenarioHazardCalculator,
    'scenario_damage': ScenarioHazardCalculator,
    'uhs': UHSCalculator,
}

CALCULATORS_NEXT = {
    'classical': ClassicalHazardCalculator,
    'event_based': EventBasedHazardCalculator,
}
