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

import numpy
from openquake.baselib import general
from openquake.commonlib import readinput
from openquake.commonlib.calculators import calculators, base


def classical_risk(riskinputs, riskmodel, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinputs:
        a list of :class:`openquake.risklib.workflows.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.workflows.RiskModel` instance
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    """
    with monitor:
        result = general.AccumDict()
        for loss_type, out in riskmodel.gen_outputs(riskinputs):
            for asset, average_losses in zip(out.assets, out.average_losses):
                result += {('avg_loss', asset.id): average_losses}
    return result


@calculators.add('classical_risk')  # from CSV
class ClassicalRiskCalculator(base.BaseRiskCalculator):
    """
    Classical Risk calculator
    """
    core_func = classical_risk

    def filter_hcurves(self, hcurves_by_imt, indices):
        """
        Reduce the hazard curves to the sites where there are assets.
        Add the intensity measure levels to the poes.

        :param hcurves_by_imt: a dictionary imt -> poes
        :param indices: an array of indices
        :returns:  a dictionary imt -> [(iml, poes), ...]
        """
        h = {}
        imtls = self.oqparam.intensity_measure_types_and_levels
        for imt, hcurves in hcurves_by_imt.iteritems():
            curves = [zip(imtls[imt], hcurve) for hcurve in hcurves[indices]]
            h[imt] = numpy.array(curves, float)
        return h

    def pre_execute(self):
        """
        Associate the assets to the sites and build the riskinputs.
        """
        super(ClassicalRiskCalculator, self).pre_execute()
        sites, hcurves_by_imt = readinput.get_sitecol_hcurves(self.oqparam)
        logging.info('Associating assets -> sites')
        with self.monitor('assoc_assets_sites'):
            sitecol, assets_by_site = self.assoc_assets_sites(sites)
        num_assets = sum(len(assets) for assets in assets_by_site)
        num_sites = len(sitecol)
        logging.info('Associated %d assets to %d sites', num_assets, num_sites)
        hcurves_by_imt = self.filter_hcurves(hcurves_by_imt, sitecol.indices)
        self.riskinputs = self.build_riskinputs(hcurves_by_imt)

    def post_execute(self, result):
        """
        Export the results. TO BE IMPLEMENTED.
        """
        for k, v in result.iteritems():
            print k, v
        return {}
