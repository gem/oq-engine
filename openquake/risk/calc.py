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


from openquake.risk.job.classical_psha import ClassicalPSHABasedMixin
from openquake.risk.job.probabilistic import ProbabilisticEventMixin
from openquake.risk.job.scenario import ScenarioEventBasedMixin


CALCULATORS = dict()


def _load_calcs():
    calcs = {
        'Classical': ClassicalPSHABasedMixin,
        'Classical BCR': ClassicalPSHABasedMixin,
        'Event Based': ProbabilisticEventMixin,
        'Event Based BCR': ProbabilisticEventMixin,
        'Scenario': ScenarioEventBasedMixin,
    }
    CALCULATORS.update(calcs)


_load_calcs()
