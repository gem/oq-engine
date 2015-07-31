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

import numpy

from openquake.baselib.general import AccumDict, humansize
from openquake.commonlib.calculators import base
from openquake.commonlib import readinput, parallel, datastore
from openquake.risklib import riskinput
from openquake.commonlib.parallel import apply_reduce

elt_dt = numpy.dtype([('rup_id', numpy.uint32), ('loss', numpy.float32)])


def cube(O, L, R, factory):
    """
    :param O: the number of different outputs
    :param L: the number of loss types
    :param R: the number of realizations
    :param factory: thunk used to initialize the elements
    :returns: a numpy array of shape (O, L, R)
    """
    losses = numpy.zeros((O, L, R), object)
    for o in range(O):
        for l in range(L):
            for r in range(R):
                losses[o, l, r] = factory()
    return losses


@parallel.litetask
def ebr(riskinputs, riskmodel, rlzs_assoc, monitor):
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
        a numpy array of shape (O, L, R); each element is a list containing
        a single array of dtype elt_dt, or an empty list
    """
    lt_idx = {lt: lti for lti, lt in enumerate(riskmodel.get_loss_types())}
    losses = cube(
        monitor.num_outputs, len(lt_idx), len(rlzs_assoc.realizations),
        AccumDict)
    for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc, monitor):
        rup_slice = out_by_rlz.rup_slice
        rup_ids = range(rup_slice.start, rup_slice.stop)
        for out in out_by_rlz:
            lti = lt_idx[out.loss_type]
            agg_losses = out.event_loss_per_asset.sum(axis=1)
            agg_ins_losses = out.insured_loss_per_asset.sum(axis=1)
            for rup_id, loss, ins_loss in zip(
                    rup_ids, agg_losses, agg_ins_losses):
                if loss > 0:
                    losses[0, lti, out.hid] += {rup_id: loss}
                if ins_loss > 0:
                    losses[1, lti, out.hid] += {rup_id: ins_loss}
    for idx, dic in numpy.ndenumerate(losses):
        if dic:
            losses[idx] = [numpy.array(dic.items(), elt_dt)]
        else:
            losses[idx] = []
    return losses


@base.calculators.add('ebr')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the event loss table only.
    """
    pre_calculator = 'event_based_rupture'
    core_func = ebr

    epsilon_matrix = datastore.persistent_attribute('epsilon_matrix')
    is_stochastic = True

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some datasets in the datastore.
        """
        super(EventBasedRiskCalculator, self).pre_execute()
        if not self.riskmodel:  # there is no riskmodel, exit early
            self.execute = lambda: None
            self.post_execute = lambda result: None
            return
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

        # preparing empty datasets
        loss_types = self.riskmodel.get_loss_types()
        self.L = len(loss_types)
        self.R = len(self.rlzs_assoc.realizations)
        self.outs = ['event_loss_table-rlzs']
        if oq.insured_losses:
            self.outs.append('insured_loss_table-rlzs')
        self.datasets = {}
        for o, out in enumerate(self.outs):
            self.datastore.hdf5.create_group(out)
            for l, loss_type in enumerate(loss_types):
                for r, rlz in enumerate(self.rlzs_assoc.realizations):
                    key = '/%s/rlz-%03d' % (loss_type, rlz.ordinal)
                    dset = self.datastore.create_dset(out + key, elt_dt)
                    dset.attrs['uid'] = rlz.uid
                    self.datasets[o, l, r] = dset

    def execute(self):
        """
        Run the ebr calculator in parallel and aggregate the results
        """
        self.monitor.oqparam = oq = self.oqparam
        # ugly: attaching an attribute needed in the task function
        self.monitor.num_outputs = 2 if oq.insured_losses else 1
        # attaching two other attributes used in riskinput.gen_outputs
        self.monitor.assets_by_site = self.assets_by_site
        self.monitor.num_assets = self.count_assets()
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, self.rlzs_assoc, self.monitor),
            concurrent_tasks=oq.concurrent_tasks,
            agg=self.agg,
            acc=cube(self.monitor.num_outputs, self.L, self.R, list),
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('col_id'))

    def agg(self, acc, losses):
        """
        Aggregate list of arrays in longer lists.

        :param acc: accumulator array of shape (O, L, R)
        :param losses: a numpy array of shape (O, L, R)
        """
        for idx, arrays in numpy.ndenumerate(losses):
            acc[idx].extend(arrays)
        return acc

    def post_execute(self, result):
        """
        Save the event loss table in the datastore.

        :param result:
            a numpy array of shape (O, L, R) containing lists of arrays
        """
        saved = {out: 0 for out in self.outs}
        with self.monitor('saving loss table',
                          autoflush=True, measuremem=True):
            for (o, l, r), arrays in numpy.ndenumerate(result):
                if not arrays:  # empty list
                    continue
                losses = numpy.concatenate(arrays)
                self.datasets[o, l, r].extend(losses)
                self.datastore.hdf5.flush()
                saved[self.outs[o]] += losses.nbytes
        for out in self.outs:
            self.datastore[out].attrs['nbytes'] = saved[out]
            logging.info('Saved %s in %s', humansize(saved[out]), out)
