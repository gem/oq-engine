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

from openquake.risklib import workflows, scientific, riskinput
from openquake.commonlib import readinput, parallel, datastore, logictree
from openquake.calculators import base, calc


F32 = numpy.float32


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
        :class:`openquake.baselib.performance.PerformanceMonitor` instance
    """
    lti = riskmodel.lti
    oq = monitor.oqparam
    ins = oq.insured_losses

    def lists():
        return [[] for _ in lti]
    result = dict(
        loss_curves=lists(), loss_maps=lists(), loss_fractions=lists(),
        stat_curves=lists(), stat_maps=lists(),
        stat_curves_ins=lists(), stat_maps_ins=lists())
    for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc, monitor):
        l = lti[out_by_rlz.loss_type]
        values = workflows.get_values(out_by_rlz.loss_type, out_by_rlz.assets)
        for out in out_by_rlz:
            r = out.hid
            for i, asset in enumerate(out.assets):
                aid = asset.idx
                val = values[i]
                avg = out.average_losses[i] * val
                avg_ins = (out.average_insured_losses[i] * val
                           if ins else numpy.nan)
                lcurve = (
                    out.loss_curves[i, 0] * val,
                    out.loss_curves[i, 1], avg)
                if ins:
                    lcurve += (
                        out.insured_curves[i, 0] * val,
                        out.insured_curves[i, 1], avg_ins)
                else:
                    lcurve += (None, None, None)
                result['loss_curves'][l].append((r, aid, lcurve))

                # no insured, shape (P, N)
                result['loss_maps'][l].append((r, aid, out.loss_maps[:, i]))

                # no insured, shape (D, N)
                if len(out.loss_fractions):
                    result['loss_fractions'][l].append(
                        (r, aid, out.loss_fractions[:, i]))

        # compute statistics
        if len(out_by_rlz) > 1:
            statsbuilder = scientific.StatsBuilder(
                oq.quantile_loss_curves,
                oq.conditional_loss_poes, oq.poes_disagg,
                riskmodel.curve_resolution)
            stats = statsbuilder.build(out_by_rlz)
            stat_curves, stat_maps = statsbuilder.get_curves_maps(stats)
            for asset, stat_curve, stat_map in zip(
                    out_by_rlz.assets, stat_curves[0], stat_maps[0]):
                result['stat_curves'][l].append((asset.idx, stat_curve))
                result['stat_maps'][l].append((asset.idx, stat_map))
            if ins:
                for ass, stat_curve, stat_map in zip(
                        out_by_rlz.assets, stat_curves[1], stat_maps[1]):
                    result['stat_curves_ins'][l].append((ass.idx, stat_curve))
                    result['stat_maps_ins'][l].append((ass.idx, stat_map))

    return result


@base.calculators.add('classical_risk')
class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical Risk calculator
    """
    pre_calculator = 'classical'
    avg_losses = datastore.persistent_attribute('avg_losses-rlzs')
    core_func = classical_risk

    def pre_execute(self):
        """
        Associate the assets to the sites and build the riskinputs.
        """
        if 'hazard_curves' in self.oqparam.inputs:  # read hazard from file
            haz_sitecol, haz_curves = readinput.get_hcurves(self.oqparam)
            self.read_exposure()  # define .assets_by_site
            self.read_riskmodel()
            self.sitecol, self.assets_by_site = self.assoc_assets_sites(
                haz_sitecol)
            curves_by_trt_gsim = {(0, 'FromFile'): haz_curves}
            self.rlzs_assoc = logictree.trivial_rlzs_assoc()
            self.save_mesh()
        else:  # compute hazard
            super(ClassicalRiskCalculator, self).pre_execute()
            logging.info('Preparing the risk input')
            curves_by_trt_gsim = {}
            for dset in self.datastore['curves_by_sm'].values():
                for key, curves in dset.items():
                    trt_id, gsim = key.split('-')
                    curves_by_trt_gsim[int(trt_id), gsim] = curves.value
        self.assetcol = riskinput.build_asset_collection(
            self.assets_by_site, self.oqparam.time_event)
        self.riskinputs = self.build_riskinputs(curves_by_trt_gsim)
        self.monitor.oqparam = self.oqparam

    def post_execute(self, result):
        """
        Save the losses in a compact form.
        """
        self.C = self.riskmodel.curve_resolution
        self.N = sum(len(assets) for assets in self.assets_by_site)
        self.L = len(self.riskmodel.loss_types)
        self.R = len(self.rlzs_assoc.realizations)
        self.I = self.oqparam.insured_losses
        self.Q1 = len(self.oqparam.quantile_loss_curves) + 1

        # save loss curves
        for l in range(self.L):
            self.save_loss_curves(l, result)

        # save loss maps and fractions (no insured)
        if self.oqparam.conditional_loss_poes:
            for l in range(self.L):
                self.save_loss_maps_and_fractions(l, result)

    def save_loss_curves(self, l, result):
        """
        Saving loss curves in the datastore.

        :param l: loss type index
        :param result: aggregated result of the task classical_risk
        """
        loss_type = self.riskmodel.loss_types[l]
        loss_curves = calc.build_loss_curves(
            (self.N, self.R), self.C, self.I)
        for r, aid, lcurve in result['loss_curves'][l]:
            for i, name in enumerate(loss_curves.dtype.names):
                loss_curves[name][aid, r] = lcurve[i]
        self.datastore['loss_curves-rlzs/' + loss_type] = loss_curves

        # loss curves stats
        if self.R > 1:
            stat_curves = calc.build_loss_curves(
                (self.Q1, self.N), self.C, self.I)
            for insflag in range(self.I + 1):
                ins = '_ins' if insflag else ''
                for aid, statcurve in result['stat_curves' + ins][l]:
                    for name in loss_curves.dtype.names:
                        for s in range(self.Q1):
                            stat_curves[name + ins][s, aid, l] = (
                                statcurve[name][s])
            self.datastore['loss_curves-stats/' + loss_type] = stat_curves

    def save_loss_maps_and_fractions(self, l, result):
        """
        Saving loss maps and fractions in the datastore.

        :param l: loss type index
        :param result: aggregated result of the task classical_risk
        """
        clp = self.oqparam.conditional_loss_poes
        loss_type = self.riskmodel.loss_types[l]
        loss_maps = calc.build_loss_maps((self.N, self.R), clp)
        for i, name in enumerate(loss_maps.dtype.names):
            lmap = loss_maps[name]
            for r, aid, lmaps in result['loss_maps'][l]:
                lmap[aid, r] = lmaps[i]
        self.datastore['loss_maps-rlzs/' + loss_type] = loss_maps

        # loss maps stats
        if self.R > 1:
            stat_maps = calc.build_loss_maps(
                (self.Q1, self.N), clp, self.I)
            for insflag in range(self.I + 1):
                ins = '_ins' if insflag else ''
                for aid, statmap in result['stat_maps' + ins][l]:
                    for name in loss_maps.dtype.names:
                        for s in range(self.Q1):
                            stat_maps[name + ins][s, aid] = statmap[name][s]
            self.datastore['loss_maps-stats/' + loss_type] = stat_maps

        # loss fractions (no insured)
        poes_disagg = self.oqparam.poes_disagg
        if poes_disagg:

            loss_fractions = calc.build_loss_maps(
                (self.N, self.R), poes_disagg)
            for i, name in enumerate(loss_fractions.dtype.names):
                lmap = loss_fractions[name]
                for r, aid, lfractions in result['loss_fractions'][l]:
                    lmap[aid, r] = lfractions[i]
            self.datastore['loss_fractions-rlzs/' + loss_type] = loss_fractions

        # TODO: should I add the loss_fractions-stats?
        # should I remove the loss fractions at all?
