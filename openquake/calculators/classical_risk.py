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
from openquake.hazardlib.stats import compute_stats
from openquake.risklib import scientific
from openquake.commonlib import readinput, source, calc
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
        r = outputs.r
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
    rlzs = riskinput.rlzs
    if len(rlzs) > 1 and param['stats']:
        statnames, stats = zip(*param['stats'])
        l_idxs = range(len(riskmodel.lti))
        for assets, rows in groupby(
                all_outputs, lambda o: tuple(o.assets)).items():
            weights = [rlzs[row.r].weight for row in rows]
            row = rows[0]
            for l in l_idxs:
                for i, asset in enumerate(assets):
                    avgs = numpy.array([r.average_losses[l][i] for r in rows])
                    avg_stats = compute_stats(avgs, stats, weights)
                    # row is index by the loss type index l and row[l]
                    # is a pair loss_curves, insured_loss_curves
                    # loss_curves[i, 0] are the i-th losses,
                    # loss_curves[i, 1] are the i-th poes
                    losses = row[l][0][i, 0]
                    poes_stats = compute_stats(
                        numpy.array([row[l][0][i, 1] for row in rows]),
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
            haz_sitecol, haz_curves = readinput.get_hcurves(oq)
            self.save_params()
            self.read_exposure()  # define .assets_by_site
            self.load_riskmodel()
            self.sitecol, self.assetcol = self.assoc_assets_sites(haz_sitecol)
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()
            rlzs = self.rlzs_assoc.realizations
            curves = {rlzs[0]: haz_curves}  # there is one realization
        else:  # compute hazard or read it from the datastore
            super(ClassicalRiskCalculator, self).pre_execute()
            if 'poes' not in self.datastore:  # when building short report
                return
            logging.info('Combining the hazard curves')
            pgetter = calc.PmapGetter(self.datastore)
            sids = self.sitecol.complete.sids
            with self.monitor(
                    'combining hcurves', measuremem=True, autoflush=True):
                pmaps = pgetter.get_pmaps(sids)
                rlzs = self.rlzs_assoc.realizations
                curves = {rlz: pmap.convert(oq.imtls, len(sids))
                          for rlz, pmap in zip(rlzs, pmaps)}
        with self.monitor('build riskinputs', measuremem=True, autoflush=True):
            self.riskinputs = self.build_riskinputs('poe', curves)
        self.param = dict(insured_losses=oq.insured_losses,
                          stats=oq.risk_stats())
        self.N = len(self.assetcol)
        self.L = len(self.riskmodel.loss_types)
        self.R = len(self.rlzs_assoc.realizations)
        self.I = oq.insured_losses
        self.S = len(oq.risk_stats())

    def post_execute(self, result):
        """
        Saving loss curves in the datastore.

        :param result: aggregated result of the task classical_risk
        """
        loss_ratios = {cb.loss_type: cb.curve_resolution
                       for cb in self.riskmodel.curve_builder
                       if cb.user_provided}
        self.loss_curve_dt, _ = scientific.build_loss_dtypes(
            loss_ratios, self.oqparam.conditional_loss_poes, self.I)
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
            stat_curves = numpy.zeros((self.N, self.S), self.loss_curve_dt)
            for l, aid, losses, statpoes, statloss in result['stat_curves']:
                stat_curves_lt = stat_curves[ltypes[l]]
                for s in range(self.S):
                    stat_curves_lt['avg'][aid, s] = statloss[s]
                    base.set_array(stat_curves_lt['poes'][aid, s], statpoes[s])
                    base.set_array(stat_curves_lt['losses'][aid, s], losses)
            self.datastore['loss_curves-stats'] = stat_curves
            self.datastore.set_nbytes('loss_curves-stats')
