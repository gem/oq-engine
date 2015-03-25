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

import logging

from openquake.baselib import general
from openquake.commonlib import readinput
from openquake.commonlib.calculators import base


def classical_risk(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        associations (trt_id, gsim) -> realizations
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    """
    with monitor:
        result = general.AccumDict()
        for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc):
            for rlz, out in out_by_rlz.iteritems():
                for asset, average_loss in zip(out.assets, out.average_losses):
                    result += {('avg_loss', rlz.ordinal, asset.id):
                               out.average_loss}
    return result


@base.calculators.add('classical_risk')
class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical Risk calculator
    """
    hazard_calculator = 'classical'
    core_func = classical_risk

    def pre_execute(self):
        """
        Associate the assets to the sites and build the riskinputs.
        """
        super(ClassicalRiskCalculator, self).pre_execute()
        hazard_from_csv = 'hazard_curves' in self.oqparam.inputs
        if hazard_from_csv:
            self.sitecol, hcurves_by_imt = readinput.get_sitecol_hcurves(
                self.oqparam)

        logging.info('Associating assets -> sites')
        with self.monitor('assoc_assets_sites'):
            sitecol, assets_by_site = self.assoc_assets_sites(self.sitecol)
        num_assets = sum(len(assets) for assets in assets_by_site)
        num_sites = len(sitecol)
        logging.info('Associated %d assets to %d sites', num_assets, num_sites)

        haz_out, _hcalc = base.get_hazard(self)
        logging.info('Preparing the risk input')
        self.rlzs_assoc = haz_out['rlzs_assoc']
        self.riskinputs = self.build_riskinputs(
            haz_out['curves_by_trt_gsim'], eps_dict={})

    def post_execute(self, result):
        """
        Export the results. TO BE IMPLEMENTED.
        """
        for k, v in result.iteritems():
            print k, v
        return {}
