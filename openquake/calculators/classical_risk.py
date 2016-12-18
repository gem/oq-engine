# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

import logging

import numpy

from openquake.baselib.general import groupby
from openquake.risklib import scientific, riskinput
from openquake.commonlib import readinput, source
from openquake.calculators import base


F32 = numpy.float32


def by_l_assets(output):
    # use loss_type index and assets as a composity key
    return output.lr[0], tuple(output.assets)


def classical_risk(riskinput, riskmodel, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    """
    oq = monitor.oqparam
    ins = oq.insured_losses
    result = dict(
        loss_curves=[], loss_maps=[], stat_curves=[], stat_maps=[])
    outputs = list(riskmodel.gen_outputs(riskinput, monitor))
    for out in outputs:
        l, r = out.lr
        for i, asset in enumerate(out.assets):
            aid = asset.ordinal
            avg = out.average_losses[i]
            avg_ins = (out.average_insured_losses[i]
                       if ins else numpy.nan)
            lcurve = (
                out.loss_curves[i, 0],
                out.loss_curves[i, 1], avg)
            if ins:
                lcurve += (
                    out.insured_curves[i, 0],
                    out.insured_curves[i, 1], avg_ins)
            else:
                lcurve += (None, None, None)
            result['loss_curves'].append((l, r, aid, lcurve))

        # compute statistics
        if len(riskinput.rlzs) > 1:
            for (l, assets), outs in groupby(outputs, by_l_assets).items():
                weights = []
                for out in outs:  # outputs with the same loss type and assets
                    weights.append(riskinput.rlzs[out.lr[1]].weight)
                for i, asset in enumerate(assets):
                    avg_stat = scientific.compute_mq(
                        numpy.array([out.average_losses for out in outs]),
                        oq.quantile_loss_curves, weights)
                    losses = out.loss_curves[i, 0]
                    poes_stat = scientific.compute_mq(
                        numpy.array([out.loss_curves[i, 1] for out in outs]),
                        oq.quantile_loss_curves, weights)
                    result['stat_curves'].append(
                        (l, asset.ordinal, losses, poes_stat, avg_stat))

    return result


@base.calculators.add('classical_risk')
class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical Risk calculator
    """
    pre_calculator = 'classical'
    core_task = classical_risk

    def pre_execute(self):
        """
        Associate the assets to the sites and build the riskinputs.
        """
        oq = self.oqparam
        if 'hazard_curves' in oq.inputs:  # read hazard from file
            haz_sitecol, haz_curves = readinput.get_hcurves(oq)
            self.save_params()
            self.read_exposure()  # define .assets_by_site
            self.load_riskmodel()
            self.assetcol = riskinput.AssetCollection(
                self.assets_by_site, self.cost_calculator,
                oq.time_event)
            self.sitecol, self.assets_by_site = self.assoc_assets_sites(
                haz_sitecol)
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()
            [rlz] = self.rlzs_assoc.realizations
            curves_by_rlz = {rlz: haz_curves}
        else:  # compute hazard or read it from the datastore
            super(ClassicalRiskCalculator, self).pre_execute()
            logging.info('Preparing the risk input')
            curves_by_rlz = {}
            nsites = len(self.sitecol.complete)
            if 'hcurves' not in self.datastore:  # when building short report
                return
            for key in self.datastore['hcurves']:
                pmap = self.datastore['hcurves/' + key]
                rlz = self.rlzs_assoc.get_rlz(key)
                if rlz is not None:  # can be None if a realization is
                    # missing; this happen in test_case_5
                    curves_by_rlz[rlz] = pmap.convert(oq.imtls, nsites)
        self.riskinputs = self.build_riskinputs(curves_by_rlz)
        self.monitor.oqparam = oq

        self.N = sum(len(assets) for assets in self.assets_by_site)
        self.L = len(self.riskmodel.loss_types)
        self.R = len(self.rlzs_assoc.realizations)
        self.I = oq.insured_losses
        self.Q1 = len(oq.quantile_loss_curves) + 1

    def post_execute(self, result):
        """
        Save the losses in a compact form.
        """
        loss_ratios = {cb.loss_type: cb.curve_resolution
                       for cb in self.riskmodel.curve_builders
                       if cb.user_provided}
        self.loss_curve_dt, self.loss_maps_dt = scientific.build_loss_dtypes(
            loss_ratios, self.oqparam.conditional_loss_poes, self.I)

        self.save_loss_curves(result)

    def save_loss_curves(self, result):
        """
        Saving loss curves in the datastore.

        :param result: aggregated result of the task classical_risk
        """
        ltypes = self.riskmodel.loss_types
        loss_curves = numpy.zeros((self.N, self.R), self.loss_curve_dt)
        for l, r, aid, lcurve in result['loss_curves']:
            loss_curves_lt = loss_curves[ltypes[l]]
            for i, name in enumerate(loss_curves_lt.dtype.names):
                if name.startswith('avg'):
                    loss_curves_lt[name][aid, r] = lcurve[i]
                else:  # 'losses', 'poes'
                    base.set_array(loss_curves_lt[name][aid, r], lcurve[i])
        self.datastore['loss_curves-rlzs'] = loss_curves

        # loss curves stats
        if self.R > 1:
            stat_curves = numpy.zeros((self.N, self.Q1), self.loss_curve_dt)
            for l, aid, losses, statcurve, statloss in result['stat_curves']:
                stat_curves_lt = stat_curves[ltypes[l]]
                for s in range(self.Q1):
                    stat_curves_lt['avg'][aid, s] = statloss[s]
                    base.set_array(stat_curves_lt['poes'][aid, s],
                                   statcurve[s])
                    base.set_array(stat_curves_lt['losses'][aid, s], losses)
            self.datastore['loss_curves-stats'] = stat_curves
