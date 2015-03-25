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

import os
import logging

from openquake.baselib.general import AccumDict
from openquake.commonlib import readinput
from openquake.commonlib.calculators import base
from openquake.commonlib.export import export
from openquake.commonlib.risk_writers import DmgState
from openquake.risklib import riskinput


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
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    :returns:
        a nested dictionary rlz_idx -> asset -> <damage array>
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))
    with monitor:
        result = {i: AccumDict() for i in range(len(rlzs_assoc))}
        for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc):
            for rlz, out in out_by_rlz.iteritems():
                result[rlz] += dict(zip(out.assets, out.damages))
    return result


@base.calculators.add('classical_damage')
class ClassicalDamageCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    core_func = classical_damage
    result_kind = 'damages_by_rlz'

    def pre_execute(self):
        """
        Compute the GMFs and build the riskinputs.
        """
        super(ClassicalDamageCalculator, self).pre_execute()

        logging.info('Reading hazard curves from CSV')
        sites, hcurves_by_imt = readinput.get_sitecol_hcurves(self.oqparam)

        with self.monitor('assoc_assets_sites'):
            sitecol, assets_by_site = self.assoc_assets_sites(sites)
        num_assets = sum(len(assets) for assets in assets_by_site)
        num_sites = len(sitecol)
        logging.info('Associated %d assets to %d sites', num_assets, num_sites)

        logging.info('Preparing the risk input')
        self.riskinputs = self.build_riskinputs(
            {(0, 'FromCsv'): hcurves_by_imt}, eps_dict={})
        self.rlzs_assoc = riskinput.FakeRlzsAssoc(num_rlzs=1)  # TODO: extend

    def post_execute(self, result):
        """
        Export the result in CSV format.

        :param result:
            a dictionary asset -> fractions per damage state
        """
        dmg_states = [DmgState(s, i)
                      for i, s in enumerate(self.riskmodel.damage_states)]
        exported = {}
        for rlz_idx in sorted(result):
            fname = 'damage_%d.csv' % rlz_idx
            exported += export(('classical_damage', 'csv'),
                               self.oqparam.export_dir,
                               fname, dmg_states, result[rlz_idx])
        return exported
