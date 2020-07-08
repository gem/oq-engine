# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import numpy

from openquake.baselib.general import AccumDict
from openquake.hazardlib import stats
from openquake.calculators import base, classical_risk


def classical_damage(riskinputs, crmodel, param, monitor):
    """
    Core function for a classical damage computation.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param crmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary l, r, a -> <damage array>
    """
    result = {}   # l, r, a -> array
    for ri in riskinputs:
        for out in ri.gen_outputs(crmodel, monitor):
            r = out.rlzi
            for l, loss_type in enumerate(crmodel.loss_types):
                for a, frac in zip(ri.assets['ordinal'], out[loss_type]):
                    if (l, r, a) in result:
                        result[l, r, a] += frac
                    else:
                        result[l, r, a] = numpy.array(frac)
    return result


@base.calculators.add('classical_damage')
class ClassicalDamageCalculator(classical_risk.ClassicalRiskCalculator):
    """
    Scenario damage calculator
    """
    core_task = classical_damage
    accept_precalc = ['classical']

    def post_execute(self, result):
        """
        Export the result in CSV format.

        :param result:
            a dictionary (l, r, a) -> fractions per damage state
        """
        D = len(self.crmodel.damage_states)
        damages = numpy.zeros((self.A, self.R, self.L, D), numpy.float32)
        for l, r, a in result:
            damages[a, r, l] = result[l, r, a]
        self.datastore['damages-rlzs'] = damages
        stats.set_rlzs_stats(self.datastore, 'damages',
                             assets=self.assetcol['id'],
                             loss_types=self.oqparam.loss_names,
                             dmg_state=self.crmodel.damage_states)
