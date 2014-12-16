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
import cPickle
import logging

from openquake.baselib import general
from openquake.commonlib import readinput
from openquake.commonlib.calculators import calculators, base, calc


def classical_risk(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinputs:
        a list of :class:`openquake.risklib.workflows.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.workflows.RiskModel` instance
    :param rlzs_assoc:
        associations (trt_id, gsim) -> realizations
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    """
    with monitor:
        result = general.AccumDict()
        for outputs in riskmodel.gen_outputs(riskinputs, rlzs_assoc):
            for i, out in enumerate(outputs):
                for asset, average_losses in zip(
                        out.assets, out.average_losses):
                    result += {('avg_loss', i, asset.id): average_losses}
    return result


@calculators.add('classical_risk_from_csv')
class ClassicalRiskFromCsvCalculator(base.BaseRiskCalculator):
    """
    Classical Risk calculator
    """
    core_func = classical_risk

    def pre_execute(self):
        """
        Associate the assets to the sites and build the riskinputs.
        """
        super(ClassicalRiskFromCsvCalculator, self).pre_execute()
        sites, hcurves_by_imt = readinput.get_sitecol_hcurves(self.oqparam)
        logging.info('Associating assets -> sites')
        with self.monitor('assoc_assets_sites'):
            sitecol, assets_by_site = self.assoc_assets_sites(sites)
        num_assets = sum(len(assets) for assets in assets_by_site)
        num_sites = len(sitecol)
        logging.info('Associated %d assets to %d sites', num_assets, num_sites)
        self.riskinputs = self.build_riskinputs(hcurves_by_imt)

    def post_execute(self, result):
        """
        Export the results. TO BE IMPLEMENTED.
        """
        for k, v in result.iteritems():
            print k, v
        return {}


@calculators.add('classical_risk')
class ClassicalRiskCalculator(base.BaseRiskCalculator):
    """
    Classical Risk calculator
    """
    core_func = classical_risk

    def pre_execute(self):
        """
        Associate the assets to the sites and build the riskinputs.
        """
        super(ClassicalRiskCalculator, self).pre_execute()

        logging.info('Associating assets -> sites')
        with self.monitor('assoc_assets_sites'):
            sitecol, assets_by_site = self.assoc_assets_sites(self.sitecol)
        num_assets = sum(len(assets) for assets in assets_by_site)
        num_sites = len(sitecol)
        logging.info('Associated %d assets to %d sites', num_assets, num_sites)

        # running the hazard calculation
        hc = calculators['classical'](self.oqparam, self.monitor('hazard'))
        cache = os.path.join(self.oqparam.export_dir, 'hazard.pik')
        if self.oqparam.usecache:
            with open(cache) as f:
                haz_out = cPickle.load(f)
        else:
            hc.pre_execute()
            result = hc.execute()
            haz_out = dict(result=result, rlzs_assoc=hc.rlzs_assoc)
            with open(cache, 'w') as f:
                cPickle.dump(haz_out, f)
        self.rlzs_assoc = haz_out['rlzs_assoc']

        logging.info('Preparing the risk input')
        hcurves_by_imt = calc.data_by_imt(
            haz_out['result'], self.oqparam.hazard_imtls, num_sites)
        self.riskinputs = self.build_riskinputs(hcurves_by_imt)

    def post_execute(self, result):
        """
        Export the results. TO BE IMPLEMENTED.
        """
        for k, v in result.iteritems():
            print k, v
        return {}
