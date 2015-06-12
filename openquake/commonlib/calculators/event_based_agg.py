#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

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
import collections

import numpy

from openquake.baselib.general import AccumDict, groupby
from openquake.commonlib.calculators import base
from openquake.commonlib import readinput, parallel, datastore
from openquake.risklib import riskinput
from openquake.commonlib.parallel import apply_reduce


def losses_dt(riskmodel, dtype=float):
    """
    Build a composite dtype from the loss types in the given
    riskmodel and dtype.

    :param riskmodel: a RiskModel instance
    :param dtype: a basic loss type (default float)
    """
    loss_types = riskmodel.get_loss_types()
    descr = []
    for lt in loss_types:
        descr.append(('rup_id~' + lt, numpy.uint32))
        descr.append(('loss~' + lt, dtype))
    return numpy.dtype(descr)


def convert(loss_dict, dt):
    # loss_dict has a triple key (loss_type, rlz_uid, rup_id)
    arraydict = {}  # rlz_uid -> composite array with rup_ids, losses
    loss_group = groupby(loss_dict, operator.itemgetter(0, 1))
    for (lt, uid), keys in loss_group.iteritems():
        rup_ids = []
        losses = []
        for key in keys:
            losses.append(loss_dict[key])
            rup_ids.append(key[2])
        if arraydict.get(uid) is None:
            arraydict[uid] = numpy.zeros(len(rup_ids), dt)
        arraydict[uid]['rup_id~' + lt] = rup_ids
        arraydict[uid]['loss~' + lt] = losses
    return arraydict


@parallel.litetask
def event_based_agg(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    :returns:
        a dictionary rlz.ordinal -> (loss_type, tag) -> AccumDict()
    """
    lt_dt = losses_dt(riskmodel)
    rlzs = rlzs_assoc.realizations
    losses = collections.defaultdict(float)  # loss_type, rlz, rup_id -> list
    ins_losses = collections.defaultdict(float)  # idem
    for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc, monitor):
        rup_slice = out_by_rlz.rup_slice
        rup_ids = range(rup_slice.start, rup_slice.stop)
        for rlz, out in zip(rlzs, out_by_rlz):
            lt = out.loss_type
            agg_losses = out.event_loss_per_asset.sum(axis=1)
            agg_ins_losses = out.insured_loss_per_asset.sum(axis=1)
            for rup_id, loss, ins_loss in zip(
                    rup_ids, agg_losses, agg_ins_losses):
                if loss > 0:
                    losses[lt, rlz.uid, rup_id] += loss
                if ins_loss > 0:
                    ins_losses[lt, rlz.uid, rup_id] += ins_loss
    return convert(losses, lt_dt), convert(ins_losses, lt_dt)


def _mean_quantiles(quantiles):
    yield 'mean'
    for q in quantiles:
        yield 'quantile-%s' % q


def _loss_map_names(conditional_loss_poes):
    names = []
    for clp in conditional_loss_poes:
        names.append('poe~%s' % clp)
    return names


@base.calculators.add('event_based_agg')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    pre_calculator = 'event_based_rupture'
    core_func = event_based_agg

    epsilon_matrix = datastore.persistent_attribute('/epsilon_matrix')
    event_loss_table = datastore.persistent_attribute(
        '/event_loss_table-rlzs')
    insured_loss_table = datastore.persistent_attribute(
        '/insured_loss_table-rlzs')
    is_stochastic = True

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some empty files in the export directory to store the gmfs
        (if any). If there were pre-existing files, they will be erased.
        """
        super(EventBasedRiskCalculator, self).pre_execute()

        oq = self.oqparam
        epsilon_sampling = oq.epsilon_sampling
        correl_model = readinput.get_correl_model(oq)
        gsims_by_col = self.rlzs_assoc.get_gsims_by_col()
        assets_by_site = self.assets_by_site

        logging.info('Populating the risk inputs')
        rup_by_tag = sum(self.datastore['sescollection'], AccumDict())
        all_ruptures = [rup_by_tag[tag] for tag in sorted(rup_by_tag)]
        num_samples = min(len(all_ruptures), epsilon_sampling)
        eps_dict = riskinput.make_eps_dict(
            assets_by_site, num_samples, oq.master_seed, oq.asset_correlation)
        logging.info('Generated %d epsilons', num_samples * len(eps_dict))
        self.epsilon_matrix = numpy.array(
            [eps_dict[a['asset_ref']] for a in self.assetcol])
        self.riskinputs = list(self.riskmodel.build_inputs_from_ruptures(
            self.sitecol.complete, all_ruptures, gsims_by_col,
            oq.truncation_level, correl_model, eps_dict,
            oq.concurrent_tasks or 1))
        logging.info('Built %d risk inputs', len(self.riskinputs))

        dt = losses_dt(self.riskmodel)
        for rlz in self.rlzs_assoc.realizations:
            self.datastore.hdf5.create_dataset(
                '/event_loss_table-rlzs/%s' % rlz.uid, (0,), dt,
                chunks=True, maxshape=(None,))
            if oq.insured_losses:
                self.datastore.hdf5.create_dataset(
                    '/insured_loss_table-rlzs/%s' % rlz.uid, (0,), dt,
                    chunks=True, maxshape=(None,))

    def execute(self):
        with self.monitor('execute risk', autoflush=True) as monitor:
            monitor.oqparam = oq = self.oqparam
            if self.pre_calculator == 'event_based_rupture':
                monitor.assets_by_site = self.assets_by_site
                monitor.num_assets = self.count_assets()
            counts_by_rlz = {rlz.uid: [0, 0]
                             for rlz in self.rlzs_assoc.realizations}
            apply_reduce(
                self.core_func.__func__,
                (self.riskinputs, self.riskmodel, self.rlzs_assoc, monitor),
                concurrent_tasks=oq.concurrent_tasks,
                agg=self.agg, acc=counts_by_rlz,
                weight=operator.attrgetter('weight'),
                key=operator.attrgetter('col_id'))

    def post_execute(self, result):
        pass

    def agg(self, acc, result):
        """
        Save the elt and ilt matrices on the HDF5 output as soon as they
        arrive from the worker.

        :param acc: dictionary rlz_uid -> slice
        """
        losses_by_rlz, ins_losses_by_rlz = result
        oq = self.oqparam
        with self.monitor('saving aggregated losses',
                          autoflush=True, measuremem=True):
            for uid, losses in losses_by_rlz.iteritems():
                n = acc[uid][0]
                elt = self.event_loss_table[uid]
                n1 = n + len(losses)
                elt.resize((n1,))
                elt[n:n1] = losses
                acc[uid][0] = n1
            if oq.insured_losses:
                for uid, ins_losses in ins_losses_by_rlz.iteritems():
                    m = acc[uid][1]
                    ilt = self.insured_loss_table[uid]
                    m1 = m + len(ins_losses)
                    ilt.resize((m1,))
                    ilt[m:m1] = ins_losses
                    acc[uid][1] = m1
            self.datastore.hdf5.flush()
        return acc
