# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""Information about the calculators available for the Risk engine."""


from openquake.calculators.risk.classical.core import ClassicalRiskCalculator
from openquake.calculators.risk.event_based.core import (
    EventBasedRiskCalculator)
from openquake.calculators.risk.scenario.core import ScenarioRiskCalculator


CALCULATORS = {
    'classical': ClassicalRiskCalculator,
    'classical_bcr': ClassicalRiskCalculator,
    'event_based': EventBasedRiskCalculator,
    'event_based_bcr': EventBasedRiskCalculator,
    'scenario': ScenarioRiskCalculator,
}
