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
import operator

import numpy

from openquake.baselib import general
from openquake.risklib import workflows, riskinput
from openquake.commonlib import readinput, parallel, datastore
from openquake.commonlib.calculators import base


@parallel.litetask
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
    result = general.AccumDict({rlz.ordinal: general.AccumDict()
                                for rlz in rlzs_assoc.realizations})
    for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc, monitor):
        for out in out_by_rlz:
            values = workflows.get_values(out.loss_type, out.assets)
            for i, asset in enumerate(out.assets):
                if out.average_insured_losses is not None:
                    ins = out.average_insured_losses[i] * values[i]
                else:
                    ins = numpy.nan
                result[out.hid][out.loss_type, asset.id] = (
                    out.average_losses[i] * values[i], ins)
    return result


@base.calculators.add('classical_risk')
class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical Risk calculator
    """
    pre_calculator = 'classical'
    avg_losses = datastore.persistent_attribute('/avg_losses/rlzs')
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
            self.sitecol, self.assets_by_site = \
                self.assoc_assets_sites(self.sitecol)

        logging.info('Preparing the risk input')
        self.riskinputs = self.build_riskinputs(
            self.datastore['curves_by_trt_gsim'])

    def post_execute(self, result):
        """
        Save the losses in a compact form.

        :param result:
            a dictionary rlz_idx -> (loss_type, asset_id) -> (avg, ins)
        """
        fields = []
        for loss_type in self.riskmodel.get_loss_types():
            fields.append(('avg_loss~%s' % loss_type, float))
            fields.append(('ins_loss~%s' % loss_type, float))
        avg_loss_dt = numpy.dtype(fields)
        num_rlzs = len(self.rlzs_assoc.realizations)
        assets = riskinput.sorted_assets(self.assets_by_site)
        self.asset_no_by_id = {a.id: no for no, a in enumerate(assets)}
        avg_losses = numpy.zeros(
            (num_rlzs, len(self.asset_no_by_id)), avg_loss_dt)

        for rlz_no in result:
            losses_by_lt_asset = result[rlz_no]
            by_asset = operator.itemgetter(1)
            for asset, keys in general.groupby(
                    losses_by_lt_asset, by_asset).iteritems():
                asset_no = self.asset_no_by_id[asset]
                losses = []
                for (loss_type, _) in keys:
                    losses.extend(losses_by_lt_asset[loss_type, asset])
                avg_losses[rlz_no][asset_no] = tuple(losses)

        self.avg_losses = avg_losses
