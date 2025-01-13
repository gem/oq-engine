# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
from openquake.hazardlib.stats import compute_stats
from openquake.risklib import scientific
from openquake.calculators import base


F32 = numpy.float32


def classical_risk(riskinputs, oqparam, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param oqparam:
        input parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    """
    crmodel = monitor.read('crmodel')
    result = dict(loss_curves=[], stat_curves=[])
    weights = oqparam._weights[:, -1]
    _statnames, stats = zip(*oqparam._stats)
    mon = monitor('getting hazard', measuremem=False)
    for ri in riskinputs:
        A = len(ri.asset_df)
        L = len(crmodel.lti)
        R = ri.hazard_getter.R
        loss_curves = numpy.zeros((R, L, A), object)
        avg_losses = numpy.zeros((R, L, A))
        with mon:
            haz = ri.hazard_getter.get_hazard()
        for taxo, asset_df in ri.asset_df.groupby('taxonomy'):
            for rlz in range(R):
                hcurve = haz[:, rlz]
                [out] = crmodel.get_outputs(asset_df, hcurve)
                for li, loss_type in enumerate(crmodel.loss_types):
                    # loss_curves has shape (A, C)
                    for i, asset in enumerate(asset_df.to_records()):
                        loss_curves[rlz, li, i] = lc = out[loss_type][i]
                        aid = asset['ordinal']
                        avg = scientific.average_loss(lc)
                        avg_losses[rlz, li, i] = avg
                        lcurve = (lc['loss'], lc['poe'], avg)
                        result['loss_curves'].append((li, rlz, aid, lcurve))

        # compute statistics
        for li, loss_type in enumerate(crmodel.loss_types):
            avg_stats = compute_stats(avg_losses[:, li], stats, weights)
            for i, asset in enumerate(ri.asset_df.to_records()):
                losses = loss_curves[0, li, i]['loss']
                all_poes = numpy.array(
                    [loss_curves[r, li, i]['poe'] for r in range(R)])
                poes_stats = compute_stats(all_poes, stats, weights)
                result['stat_curves'].append(
                    (li, asset['ordinal'], losses, poes_stats, avg_stats[:, i]))
    if R == 1:  # the realization is the same as the mean
        del result['loss_curves']
    return result


@base.calculators.add('classical_risk')
class ClassicalRiskCalculator(base.RiskCalculator):
    """
    Classical Risk calculator
    """
    core_task = classical_risk
    precalc = 'classical'
    accept_precalc = ['classical']

    def pre_execute(self):
        """
        Associate the assets to the sites and build the riskinputs.
        """
        oq = self.oqparam
        super().pre_execute()
        parent = self.datastore.parent
        if '_rates' in self.datastore or '_rates' in parent:
            full_lt = self.datastore['full_lt'].init()
            stats = list(oq.hazard_stats().items())
            oq._stats = stats
            oq._weights = full_lt.weights
            self.riskinputs = self.build_riskinputs()
            self.A = len(self.assetcol)
            self.L = len(self.crmodel.loss_types)
            self.S = len(oq.hazard_stats())

    def post_execute(self, result):
        """
        Saving loss curves in the datastore.

        :param result: aggregated result of the task classical_risk
        """
        curve_res = {cp.loss_type: cp.curve_resolution
                     for cp in self.crmodel.curve_params
                     if cp.user_provided}
        self.loss_curve_dt = scientific.build_loss_curve_dt(
            curve_res, insurance_losses=False)
        ltypes = self.crmodel.loss_types

        # loss curves stats are generated always
        stats = list(self.oqparam.hazard_stats())
        stat_curves = numpy.zeros((self.A, self.S), self.loss_curve_dt)
        avg_losses = numpy.zeros((self.A, self.S, self.L), F32)
        for li, a, losses, statpoes, statloss in result['stat_curves']:
            stat_curves_lt = stat_curves[ltypes[li]]
            for s in range(self.S):
                avg_losses[a, s, li] = statloss[s]
                base.set_array(stat_curves_lt['poes'][a, s], statpoes[s])
                base.set_array(stat_curves_lt['losses'][a, s], losses)
        for li, lt in enumerate(ltypes):
            self.datastore['avg_losses-stats/' + lt] = avg_losses[:, :, li]
            self.datastore.set_shape_descr(
                'avg_losses-stats/' + lt,
                asset_id=self.assetcol['id'], stat=stats)
        self.datastore['loss_curves-stats'] = stat_curves
        self.datastore.set_attrs('loss_curves-stats', stat=stats)

        if self.R > 1:  # individual realizations saved only if many
            loss_curves = numpy.zeros((self.A, self.R), self.loss_curve_dt)
            avg_losses = numpy.zeros((self.A, self.R, self.L), F32)
            for li, r, a, (losses, poes, avg) in result['loss_curves']:
                lc = loss_curves[a, r][ltypes[li]]
                avg_losses[a, r, li] = avg
                base.set_array(lc['losses'], losses)
                base.set_array(lc['poes'], poes)
            for li, lt in enumerate(ltypes):
                self.datastore['avg_losses-rlzs/' + lt] = avg_losses[:, :, li]
                self.datastore.set_shape_descr(
                    'avg_losses-rlzs/' + lt,
                    asset_id=self.assetcol['id'], rlz=numpy.arange(self.R))
            self.datastore['loss_curves-rlzs'] = loss_curves
