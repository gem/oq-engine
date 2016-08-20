import math
import operator
import collections
import logging
import numpy

from openquake.baselib import general
from openquake.commonlib import parallel
from openquake.risklib import riskinput
from openquake.calculators.event_based_risk import base

F32 = numpy.float32


def ebr_agg(riskinput, riskmodel, monitor):
    """
    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary aid -> average losses of shape (L, R, I)
    """
    lti = riskmodel.lti  # loss type -> index
    L = len(lti)
    R = monitor.num_rlzs
    I = monitor.I
    result = {aid: numpy.zeros((L, R, I), F32) for aid in riskinput.aids}
    for output in riskmodel.gen_outputs(riskinput, None, monitor):
        for (l, r), out in sorted(output.items()):
            loss_type = riskmodel.loss_types[l]
            for i, asset in enumerate(output.assets):
                loss_ratios = out.loss_ratios[i]  # shape (E, I)
                losses = loss_ratios * asset.value(loss_type)
                result[asset.ordinal][l, r] += losses.sum(axis=0)
    return result


@base.calculators.add('ebr_from_gmfs')
class EventBasedRiskFromGmfsCalculator(base.RiskCalculator):
    pre_calculator = 'event_based'
    is_stochastic = True

    def build_riskinputs(self, gmfcoll, eps={}):
        mon = self.monitor('reading gmfs')
        imtls = self.oqparam.imtls
        if not set(self.oqparam.risk_imtls) & set(imtls):
            rsk = ', '.join(self.oqparam.risk_imtls)
            haz = ', '.join(imtls)
            raise ValueError('The IMTs in the risk models (%s) are disjoint '
                             "from the IMTs in the hazard (%s)" % (rsk, haz))
        num_tasks = math.ceil(self.oqparam.concurrent_tasks / len(imtls))
        with self.monitor('building riskinputs', autoflush=True):
            idx_weight_pairs = [
                (i, len(assets))
                for i, assets in enumerate(self.assets_by_site)]
            blocks = general.split_in_blocks(
                idx_weight_pairs, num_tasks, weight=operator.itemgetter(1))
            for block in blocks:
                indices = numpy.array([idx for idx, _weight in block])
                sids = self.sitecol.sids[indices]
                reduced_assets = self.assets_by_site[indices]
                # dictionary of epsilons for the reduced assets
                reduced_eps = collections.defaultdict(F32)
                if len(eps):
                    for assets in reduced_assets:
                        for asset in assets:
                            reduced_eps[asset.ordinal] = eps[asset.ordinal]
                # build the riskinputs
                for imt in imtls:
                    with mon:
                        gmvs_by_site = [gmfcoll[sid, imt] for sid in sids]
                    ri = self.riskmodel.build_input(
                        imt, gmvs_by_site, reduced_assets, reduced_eps)
                    logging.info(str(ri))
                    yield ri

    def execute(self):
        monitor = self.monitor.new()
        imts = list(self.oqparam.imtls)
        rlzs = self.rlzs_assoc.realizations
        self.A = sum(map(len, self.assets_by_site))  # number of assets
        self.L = len(self.riskmodel.lti)
        self.R = monitor.num_rlzs = len(rlzs)
        self.I = monitor.I = self.oqparam.insured_losses + 1
        if self.riskmodel.covs:
            logging.warn('NB: asset correlation is ignored by %s',
                         self.__class__.__name__)

        gmfcoll = riskinput.GmfCollector(imts, rlzs, self.datastore)
        iterargs = ((ri, self.riskmodel, monitor)
                    for ri in self.build_riskinputs(gmfcoll))
        return parallel.starmap(ebr_agg, iterargs).reduce()

    def post_execute(self, result):
        for r in range(self.R):
            avglosses = numpy.zeros((self.A, self.L, self.I), F32)
            for aid in result:
                avglosses[aid] = result[aid][:, r, :]
            self.datastore['avg_losses/rlz-%04d' % r] = avglosses
