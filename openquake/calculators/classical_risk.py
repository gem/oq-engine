# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
from openquake.baselib.python3compat import encode
from openquake.hazardlib.stats import compute_stats
from openquake.risklib import scientific
from openquake.calculators import base


F32 = numpy.float32


def classical_risk(riskinputs, riskmodel, param, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    """
    result = dict(loss_curves=[], stat_curves=[])
    weights = [w['default'] for w in param['weights']]
    statnames, stats = zip(*param['stats'])
    for ri in riskinputs:
        A = len(ri.assets)
        L = len(riskmodel.lti)
        R = ri.hazard_getter.num_rlzs
        loss_curves = numpy.zeros((R, L, A), object)
        avg_losses = numpy.zeros((R, L, A))
        for out in riskmodel.gen_outputs(ri, monitor):
            r = out.rlzi
            for l, loss_type in enumerate(riskmodel.loss_types):
                # loss_curves has shape (A, C)
                for i, asset in enumerate(ri.assets):
                    loss_curves[out.rlzi, l, i] = lc = out[loss_type][i]
                    aid = asset['ordinal']
                    avg = scientific.average_loss(lc)
                    avg_losses[r, l, i] = avg
                    lcurve = (lc['loss'], lc['poe'], avg)
                    result['loss_curves'].append((l, r, aid, lcurve))

        # compute statistics
        for l, loss_type in enumerate(riskmodel.loss_types):
            for i, asset in enumerate(ri.assets):
                avg_stats = compute_stats(avg_losses[:, l, i], stats, weights)
                losses = loss_curves[0, l, i]['loss']
                all_poes = numpy.array(
                    [loss_curves[r, l, i]['poe'] for r in range(R)])
                poes_stats = compute_stats(all_poes, stats, weights)
                result['stat_curves'].append(
                    (l, asset['ordinal'], losses, poes_stats, avg_stats))
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
        if 'poes' not in self.datastore:  # when building short report
            return
        weights = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        stats = list(oq.hazard_stats().items())
        self.param = dict(stats=stats, weights=weights)
        self.riskinputs = self.build_riskinputs('poe')
        self.A = len(self.assetcol)
        self.L = len(self.riskmodel.loss_types)
        self.S = len(oq.hazard_stats())

    def post_execute(self, result):
        """
        Saving loss curves in the datastore.

        :param result: aggregated result of the task classical_risk
        """
        curve_res = {cp.loss_type: cp.curve_resolution
                     for cp in self.riskmodel.curve_params
                     if cp.user_provided}
        self.loss_curve_dt = scientific.build_loss_curve_dt(
            curve_res, insured_losses=False)
        ltypes = self.riskmodel.loss_types

        # loss curves stats are generated always
        stats = encode(list(self.oqparam.hazard_stats()))
        stat_curves = numpy.zeros((self.A, self.S), self.loss_curve_dt)
        avg_losses = numpy.zeros((self.A, self.S, self.L), F32)
        for l, a, losses, statpoes, statloss in result['stat_curves']:
            stat_curves_lt = stat_curves[ltypes[l]]
            for s in range(self.S):
                avg_losses[a, s, l] = statloss[s]
                base.set_array(stat_curves_lt['poes'][a, s], statpoes[s])
                base.set_array(stat_curves_lt['losses'][a, s], losses)
        self.datastore['avg_losses-stats'] = avg_losses
        self.datastore.set_attrs('avg_losses-stats', stats=stats)
        self.datastore['loss_curves-stats'] = stat_curves
        self.datastore.set_attrs('loss_curves-stats', stats=stats)

        if self.R > 1:  # individual realizations saved only if many
            loss_curves = numpy.zeros((self.A, self.R), self.loss_curve_dt)
            avg_losses = numpy.zeros((self.A, self.R, self.L), F32)
            for l, r, a, (losses, poes, avg) in result['loss_curves']:
                lc = loss_curves[a, r][ltypes[l]]
                avg_losses[a, r, l] = avg
                base.set_array(lc['losses'], losses)
                base.set_array(lc['poes'], poes)
            self.datastore['avg_losses-rlzs'] = avg_losses
            self.datastore['loss_curves-rlzs'] = loss_curves
