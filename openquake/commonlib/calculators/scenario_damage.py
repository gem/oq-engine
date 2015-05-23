#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014-2015, GEM Foundation

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

import os
import logging

from openquake.commonlib import parallel, datastore
from openquake.risklib import scientific
from openquake.baselib.general import AccumDict
from openquake.commonlib.calculators import base


@parallel.litetask
def scenario_damage(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    Core function for a damage computation.

    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    :returns:
        a dictionary {('asset', asset): <mean stddev>,
                      ('taxonomy', asset.taxonomy): <damage array>}
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))
    ordinals = range(len(rlzs_assoc.realizations))
    result = AccumDict({i: AccumDict() for i in ordinals})
    # ordinal -> (key_type, key) -> array
    for out_by_rlz in riskmodel.gen_outputs(
            riskinputs, rlzs_assoc, monitor):
        for out in out_by_rlz:
            for asset, fraction in zip(out.assets, out.damages):
                damages = fraction * asset.number
                result[out.hid] += {
                    ('asset', asset.id): scientific.mean_std(damages)}
                result[out.hid] += {
                    ('taxonomy', asset.taxonomy): damages}
    return result


@base.calculators.add('scenario_damage')
class ScenarioDamageCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    pre_calculator = 'scenario'
    core_func = scenario_damage
    damages_by_key = datastore.persistent_attribute('damages_by_key')
    gmf_by_trt_gsim = datastore.persistent_attribute('gmf_by_trt_gsim')

    def pre_execute(self):
        if 'gmfs' in self.oqparam.inputs:
            self.pre_calculator = None
        base.RiskCalculator.pre_execute(self)
        gmfs = base.get_gmfs(self)
        self.riskinputs = self.build_riskinputs(gmfs)

    def post_execute(self, result):
        self.damages_by_key = result
