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

"""This package contains Hazard calculator classes and utilities."""


from openquake.hazard.opensha import ClassicalMixin, EventBasedMixin
from openquake.hazard.scenario import ScenarioEventBasedMixin
from openquake.calculators.hazard.disagg.core import DisaggMixin


CALCULATORS = {
    'classical': ClassicalMixin,
    'classical_bcr': ClassicalMixin,
    'event_based': EventBasedMixin,
    'event_based_bcr': EventBasedMixin,
    'disaggregation': DisaggMixin,
    'scenario': ScenarioEventBasedMixin,
}
