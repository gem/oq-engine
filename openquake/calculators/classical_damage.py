# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
from openquake.calculators import base, classical_risk


def classical_damage(riskinput, riskmodel, param, monitor):
    """
    Core function for a classical damage computation.

    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a nested dictionary rlz_idx -> asset -> <damage array>
    """
    with monitor:
        result = {i: AccumDict() for i in range(len(riskinput.rlzs))}
        for outputs in riskmodel.gen_outputs(riskinput, monitor):
            for l, out in enumerate(outputs):
                ordinals = [a.ordinal for a in outputs.assets]
                result[outputs.r] += dict(zip(ordinals, out))
    return result


@base.calculators.add('classical_damage')
class ClassicalDamageCalculator(classical_risk.ClassicalRiskCalculator):
    """
    Scenario damage calculator
    """
    core_task = classical_damage

    def check_poes(self, curves_by_rlz):
        """
        Raise an error if one PoE = 1, since it would produce a log(0) in
        :class:`openquake.risklib.scientific.annual_frequency_of_exceedence`
        """
        for rlz, curves in curves_by_rlz.items():
            for imt in self.oqparam.imtls:
                for sid, poes in enumerate(curves[imt]):
                    if (poes == 1).any():
                        raise ValueError('Found a PoE=1 for site_id=%d, %s'
                                         % (sid, imt))

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
        self.datastore['damages-rlzs'] = damages
