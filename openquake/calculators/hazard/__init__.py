# Copyright (c) 2010-2012, GEM Foundation.
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

"""This package contains Hazard calculator classes and utilities."""


from openquake.calculators.hazard.classical.core import (
    ClassicalHazardCalculator)
from openquake.calculators.hazard.disagg.core import DisaggHazardCalculator
from openquake.calculators.hazard.event_based.core import (
    EventBasedHazardCalculator)
from openquake.calculators.hazard.scenario.core import ScenarioHazardCalculator


CALCULATORS = {
    'classical': ClassicalHazardCalculator,
    'classical_bcr': ClassicalHazardCalculator,
    'event_based': EventBasedHazardCalculator,
    'event_based_bcr': EventBasedHazardCalculator,
    'disaggregation': DisaggHazardCalculator,
    'scenario': ScenarioHazardCalculator,
}
