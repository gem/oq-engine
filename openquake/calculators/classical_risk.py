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
from openquake.calculators import base


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

    result = dict(
        loss_curves=[], loss_maps=[], stat_curves=[], stat_maps=[])
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
                result['loss_curves'].append((l, r, aid, lcurve))

                # no insured, shape (P, N)
                result['loss_maps'].append(
                    (l, r, aid, out.loss_maps[:, i] * val))

        # compute statistics
        if len(out_by_rlz) > 1:
            cb = riskmodel.curve_builders[l]
            statsbuilder = scientific.StatsBuilder(
                oq.quantile_loss_curves,
                oq.conditional_loss_poes, oq.poes_disagg,
                cb.curve_resolution, insured_losses=oq.insured_losses)
            stats = statsbuilder.build(out_by_rlz)
            stat_curves, stat_maps = statsbuilder.get_curves_maps(stats)
            for asset, stat_curve, stat_map in zip(
                    out_by_rlz.assets, stat_curves, stat_maps):
                result['stat_curves'].append((l, asset.idx, stat_curve))
                result['stat_maps'].append((l, asset.idx, stat_map))

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
            self.load_riskmodel()
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

        self.N = sum(len(assets) for assets in self.assets_by_site)
        self.L = len(self.riskmodel.loss_types)
        self.R = len(self.rlzs_assoc.realizations)
        self.I = self.oqparam.insured_losses
        self.Q1 = len(self.oqparam.quantile_loss_curves) + 1

    def post_execute(self, result):
        """
        Save the losses in a compact form.
        """
        self.loss_curve_dt, self.loss_maps_dt = (
            self.riskmodel.build_loss_dtypes(
                self.oqparam.conditional_loss_poes, self.I))

        self.save_loss_curves(result)
        if self.oqparam.conditional_loss_poes:
            self.save_loss_maps(result)

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
                loss_curves_lt[name][aid, r] = lcurve[i]
        self.datastore['loss_curves-rlzs'] = loss_curves

        # loss curves stats
        if self.R > 1:
            stat_curves = numpy.zeros((self.Q1, self.N), self.loss_curve_dt)
            for l, aid, statcurve in result['stat_curves']:
                stat_curves_lt = stat_curves[ltypes[l]]
                for name in stat_curves_lt.dtype.names:
                    for s in range(self.Q1):
                        stat_curves_lt[name][s, aid] = statcurve[name][s]
            self.datastore['loss_curves-stats'] = stat_curves

    def save_loss_maps(self, result):
        """
        Saving loss maps in the datastore.

        :param result: aggregated result of the task classical_risk
        """
        ltypes = self.riskmodel.loss_types
        loss_maps = numpy.zeros((self.N, self.R), self.loss_maps_dt)
        for l, r, aid, lmaps in result['loss_maps']:
            loss_maps_lt = loss_maps[ltypes[l]]
            for i, name in enumerate(loss_maps_lt.dtype.names):
                loss_maps_lt[name][aid, r] = lmaps[i]
        self.datastore['loss_maps-rlzs'] = loss_maps

        # loss maps stats
        if self.R > 1:
            stat_maps = numpy.zeros((self.Q1, self.N), self.loss_maps_dt)
            for l, aid, statmaps in result['stat_maps']:
                statmaps_lt = stat_maps[ltypes[l]]
                for name in statmaps_lt.dtype.names:
                    for s in range(self.Q1):
                        statmaps_lt[name][s, aid] = statmaps[name][s]
            self.datastore['loss_maps-stats'] = stat_maps
