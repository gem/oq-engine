#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy

from openquake.baselib.general import AccumDict
from openquake.commonlib import parallel, datastore
from openquake.calculators import base, classical_risk


@parallel.litetask
def classical_damage(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    Core function for a classical damage computation.

    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        associations (trt_id, gsim) -> realizations
    :param monitor:
        :class:`openquake.baselib.performance.PerformanceMonitor` instance
    :returns:
        a nested dictionary rlz_idx -> asset -> <damage array>
    """
    with monitor:
        result = {i: AccumDict() for i in range(len(rlzs_assoc))}
        for out_by_rlz in riskmodel.gen_outputs(
                riskinputs, rlzs_assoc, monitor):
            for out in out_by_rlz:
                asset_ids = [a.idx for a in out.assets]
                result[out.hid] += dict(zip(asset_ids, out.damages))
    return result


@base.calculators.add('classical_damage')
class ClassicalDamageCalculator(classical_risk.ClassicalRiskCalculator):
    """
    Scenario damage calculator
    """
    core_func = classical_damage
    damages = datastore.persistent_attribute('damages-rlzs')

    def post_execute(self, result):
        """
        Export the result in CSV format.

        :param result:
            a dictionary asset -> fractions per damage state
        """
        damages_dt = numpy.dtype([(ds, numpy.float32)
                                  for ds in self.riskmodel.damage_states])
        damages = numpy.zeros((self.N, self.R), damages_dt)
        for r in result:
            for aid, fractions in result[r].items():
                damages[aid, r] = tuple(fractions)
        self.damages = damages
