# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from openquake.baselib.general import groupby, AccumDict
from openquake.baselib.python3compat import encode
from openquake.hazardlib.stats import compute_stats
from openquake.risklib import scientific
from openquake.commonlib import readinput, source
from openquake.calculators import base


F32 = numpy.float32


def classical_risk(riskinput, riskmodel, param, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    """
    ins = param['insured_losses']
    result = dict(loss_curves=[], stat_curves=[])
    all_outputs = list(riskmodel.gen_outputs(riskinput, monitor))
    for outputs in all_outputs:
        r = outputs.rlzi
        outputs.average_losses = AccumDict(accum=[])  # l -> array
        for l, (loss_curves, insured_curves) in enumerate(outputs):
            for i, asset in enumerate(outputs.assets):
                aid = asset.ordinal
                avg = scientific.average_loss(loss_curves[i])
                outputs.average_losses[l].append(avg)
                lcurve = (loss_curves[i, 0], loss_curves[i, 1], avg)
                if ins:
                    lcurve += (
                        insured_curves[i, 0], insured_curves[i, 1],
                        scientific.average_loss(insured_curves[i]))
                else:
                    lcurve += (None, None, None)
                result['loss_curves'].append((l, r, aid, lcurve))

    # compute statistics
    R = riskinput.hazard_getter.num_rlzs
    if R > 1 and param['stats']:
        w = param['weights']
        statnames, stats = zip(*param['stats'])
        l_idxs = range(len(riskmodel.lti))
        for assets, outs in groupby(
                all_outputs, lambda o: tuple(o.assets)).items():
            weights = [w[out.rlzi] for out in outs]
            out = outs[0]
            for l in l_idxs:
                for i, asset in enumerate(assets):
                    avgs = numpy.array([r.average_losses[l][i] for r in outs])
                    avg_stats = compute_stats(avgs, stats, weights)
                    # out is index by the loss type index l and out[l]
                    # is a pair loss_curves, insured_loss_curves
                    # loss_curves[i, 0] are the i-th losses,
                    # loss_curves[i, 1] are the i-th poes
                    losses = out[l][0][i, 0]
                    poes_stats = compute_stats(
                        numpy.array([out[l][0][i, 1] for out in outs]),
                        stats, weights)
                    result['stat_curves'].append(
                        (l, asset.ordinal, losses, poes_stats, avg_stats))
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
        if oq.insured_losses:
            raise ValueError(
                'insured_losses are not supported for classical_risk')
        if 'hazard_curves' in oq.inputs:  # read hazard from file
            haz_sitecol, pmap = readinput.get_pmap(oq)
            self.datastore['poes/grp-00'] = pmap
            self.save_params()
            self.read_exposure()  # define .assets_by_site
            self.load_riskmodel()
            self.sitecol, self.assetcol = self.assoc_assets_sites(haz_sitecol)
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()
            self.before_export()  # save 'realizations' dataset
        else:  # compute hazard or read it from the datastore
            super(ClassicalRiskCalculator, self).pre_execute()
            if 'poes' not in self.datastore:  # when building short report
                return
        weights = self.datastore['realizations']['weight']
        self.R = len(weights)
        with self.monitor('build riskinputs', measuremem=True, autoflush=True):
            self.riskinputs = self.build_riskinputs('poe')
        self.param = dict(insured_losses=oq.insured_losses,
                          stats=oq.risk_stats(), weights=weights)
        self.N = len(self.assetcol)
        self.L = len(self.riskmodel.loss_types)
        self.I = oq.insured_losses
        self.S = len(oq.risk_stats())

    def post_execute(self, result):
        """
        Saving loss curves in the datastore.

        :param result: aggregated result of the task classical_risk
        """
        loss_ratios = {cp.loss_type: cp.curve_resolution
                       for cp in self.riskmodel.curve_params
                       if cp.user_provided}
        self.loss_curve_dt = scientific.build_loss_curve_dt(
            loss_ratios, self.I)
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
        self.datastore.set_nbytes('loss_curves-rlzs')

        # loss curves stats
        if self.R > 1:
            stats = [encode(n) for (n, f) in self.oqparam.risk_stats()]
            stat_curves = numpy.zeros((self.N, self.S), self.loss_curve_dt)
            for l, aid, losses, statpoes, statloss in result['stat_curves']:
                stat_curves_lt = stat_curves[ltypes[l]]
                for s in range(self.S):
                    stat_curves_lt['avg'][aid, s] = statloss[s]
                    base.set_array(stat_curves_lt['poes'][aid, s], statpoes[s])
                    base.set_array(stat_curves_lt['losses'][aid, s], losses)
            self.datastore['loss_curves-stats'] = stat_curves
            self.datastore.set_attrs(
                'loss_curves-stats', nbytes=stat_curves.nbytes, stats=stats)
