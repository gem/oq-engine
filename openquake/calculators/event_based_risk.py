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

from openquake.baselib.general import AccumDict, humansize
from openquake.calculators import base
from openquake.commonlib import readinput, parallel, datastore
from openquake.risklib import riskinput, scientific
from openquake.commonlib.parallel import apply_reduce

OUTPUTS = ['agg_losses-rlzs', 'avg_losses-rlzs', 'specific-losses-rlzs',
           'rcurves-rlzs', 'icurves-rlzs']

AGGLOSS, AVGLOSS, SPECLOSS, RC, IC = 0, 1, 2, 3, 4

elt_dt = numpy.dtype([('rup_id', numpy.uint32), ('loss', numpy.float32),
                      ('ins_loss',  numpy.float32)])
ela_dt = numpy.dtype([('rup_id', numpy.uint32), ('ass_id', numpy.uint32),
                      ('loss', numpy.float32), ('ins_loss',  numpy.float32)])


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
def event_based_risk(riskinputs, riskmodel, rlzs_assoc, monitor):
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
    lti = riskmodel.lti  # loss type -> index
    specific_assets = monitor.oqparam.specific_assets
    result = cube(
        monitor.num_outputs, len(lti), len(rlzs_assoc.realizations), list)
    for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc, monitor):
        rup_slice = out_by_rlz.rup_slice
        rup_ids = list(range(rup_slice.start, rup_slice.stop))
        for out in out_by_rlz:
            l = lti[out.loss_type]
            asset_ids = [a.idx for a in out.assets]

            # collect losses for specific assets
            specific_ids = set(a.idx for a in out.assets
                               if a.id in specific_assets)
            if specific_ids:
                for rup_id, all_losses, ins_losses in zip(
                        rup_ids, out.event_loss_per_asset,
                        out.insured_loss_per_asset):
                    for aid, sloss, iloss in zip(
                            asset_ids, all_losses, ins_losses):
                        if aid in specific_ids:
                            if sloss > 0:
                                result[SPECLOSS, l, out.hid].append(
                                    (rup_id, aid, sloss, iloss))

            # collect aggregate losses
            agg_losses = out.event_loss_per_asset.sum(axis=1)
            agg_ins_losses = out.insured_loss_per_asset.sum(axis=1)
            for rup_id, loss, ins_loss in zip(
                    rup_ids, agg_losses, agg_ins_losses):
                if loss > 0:
                    result[AGGLOSS, l, out.hid].append(
                        (rup_id, numpy.array([loss, ins_loss])))

            # dictionaries asset_idx -> array of counts
            if riskmodel.curve_builders[l].user_provided:
                result[RC, l, out.hid].append(dict(
                    zip(asset_ids, out.counts_matrix)))
                if out.insured_counts_matrix.sum():
                    result[IC, l, out.hid].append(dict(
                        zip(asset_ids, out.insured_counts_matrix)))

            # average losses
            arr = numpy.zeros((monitor.num_assets, 2))
            for aid, avgloss, ins_avgloss in zip(
                    asset_ids, out.average_losses, out.average_insured_losses):
                # NB: here I cannot use numpy.float32, because the sum of
                # numpy.float32 numbers is noncommutative!
                # the net effect is that the final loss is affected by
                # the order in which the tasks are run, which is random
                # i.e. at each run one may get different results!!
                arr[aid] = [avgloss, ins_avgloss]
            result[AVGLOSS, l, out.hid].append(arr)

    for idx, lst in numpy.ndenumerate(result):
        o, l, r = idx
        if lst:
            if o == AGGLOSS:
                acc = collections.defaultdict(float)
                for rupt, loss in lst:
                    acc[rupt] += loss
                result[idx] = [numpy.array([(rup, loss[0], loss[1])
                                            for rup, loss in acc.items()],
                                           elt_dt)]
            elif o == AVGLOSS:
                result[idx] = [sum(lst)]
            elif o == SPECLOSS:
                result[idx] = [numpy.array(lst, ela_dt)]
            else:  # risk curves
                result[idx] = [sum(lst, AccumDict())]
        else:
            result[idx] = []
    return result


@base.calculators.add('event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the event loss table and
    fixed ratios loss curves.
    """
    pre_calculator = 'event_based_rupture'
    core_func = event_based_risk

    epsilon_matrix = datastore.persistent_attribute('epsilon_matrix')
    spec_indices = datastore.persistent_attribute('spec_indices')
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
        if self.riskmodel.covs:
            epsilon_sampling = oq.epsilon_sampling
        else:
            epsilon_sampling = 1  # only one ignored epsilon
        correl_model = readinput.get_correl_model(oq)
        gsims_by_col = self.rlzs_assoc.get_gsims_by_col()
        assets_by_site = self.assets_by_site
        # the following is needed to set the asset idx attribute
        self.assetcol = riskinput.build_asset_collection(
            assets_by_site, oq.time_event)
        self.spec_indices = numpy.array([a['asset_ref'] in oq.specific_assets
                                         for a in self.assetcol])

        logging.info('Populating the risk inputs')
        rup_by_tag = sum(self.datastore['sescollection'], AccumDict())
        all_ruptures = [rup_by_tag[tag] for tag in sorted(rup_by_tag)]
        for i, rup in enumerate(all_ruptures):
            rup.ordinal = i
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
        loss_types = self.riskmodel.loss_types
        self.L = len(loss_types)
        self.R = len(self.rlzs_assoc.realizations)
        self.outs = OUTPUTS
        self.datasets = {}
        self.monitor.oqparam = self.oqparam
        # ugly: attaching an attribute needed in the task function
        self.monitor.num_outputs = len(self.outs)
        # attaching two other attributes used in riskinput.gen_outputs
        self.monitor.assets_by_site = self.assets_by_site
        self.monitor.eps_dict = eps_dict
        self.monitor.num_assets = N = self.count_assets()
        for o, out in enumerate(self.outs):
            self.datastore.hdf5.create_group(out)
            for l, loss_type in enumerate(loss_types):
                cb = self.riskmodel.curve_builders[l]
                C = len(cb.ratios)  # curve resolution
                for r, rlz in enumerate(self.rlzs_assoc.realizations):
                    key = '/%s/%s' % (loss_type, rlz.uid)
                    if o == AGGLOSS:  # loss tables
                        dset = self.datastore.create_dset(out + key, elt_dt)
                    elif o == AVGLOSS:  # average losses
                        dset = self.datastore.create_dset(
                            out + key, numpy.float32, (N, 2))
                    elif o == SPECLOSS:  # specific losses
                        dset = self.datastore.create_dset(out + key, ela_dt)
                    else:  # risk curves
                        if not C:
                            continue
                        dset = self.datastore.create_dset(
                            out + key, cb.lr_dt, N)
                    self.datasets[o, l, r] = dset
                if o == RC and C:
                    grp = self.datastore['%s/%s' % (out, loss_type)]
                    grp.attrs['loss_ratios'] = cb.ratios

    def execute(self):
        """
        Run the event_based_risk calculator and aggregate the results
        """
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, self.rlzs_assoc, self.monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            agg=self.agg,
            acc=cube(self.monitor.num_outputs, self.L, self.R, list),
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('col_id'))

    def agg(self, acc, result):
        """
        Aggregate list of arrays in longer lists.

        :param acc: accumulator array of shape (O, L, R)
        :param result: a numpy array of shape (O, L, R)
        """
        for idx, arrays in numpy.ndenumerate(result):
            # TODO: special case for avg_losses, they can be summed directly
            if idx[0] == AVGLOSS:  # arrays has only 1 element
                acc[idx] = [sum(acc[idx] + arrays)]
            else:
                acc[idx].extend(arrays)
        return acc

    def post_execute(self, result):
        """
        Save the event loss table in the datastore.

        :param result:
            a numpy array of shape (O, L, R) containing lists of arrays
        """
        ses_ratio = self.oqparam.ses_ratio
        saved = {out: 0 for out in self.outs}
        N = len(self.assetcol)
        with self.monitor('saving loss table',
                          autoflush=True, measuremem=True):
            for (o, l, r), data in numpy.ndenumerate(result):
                if not data:  # empty list
                    continue
                cb = self.riskmodel.curve_builders[l]
                if o in (AGGLOSS, SPECLOSS):  # data is a list of arrays
                    losses = numpy.concatenate(data)
                    self.datasets[o, l, r].extend(losses)
                    saved[self.outs[o]] += losses.nbytes
                elif o == AVGLOSS:  # average losses
                    lt = self.riskmodel.loss_types[l]
                    [avgloss] = data
                    avglosses = numpy.array(
                        [avgloss[i] * asset[lt]
                         for i, asset in enumerate(self.assetcol)],
                        numpy.float32)
                    self.datasets[o, l, r].dset[:] = avglosses
                    saved[self.outs[o]] += avglosses.nbytes
                elif cb.user_provided:  # risk curves
                    # data is a list of dicts asset idx -> counts
                    poes = cb.build_poes(N, data, ses_ratio)
                    self.datasets[o, l, r] = poes
                    saved[self.outs[o]] += poes.nbytes
                self.datastore.hdf5.flush()

        for out in self.outs:
            nbytes = saved[out]
            if nbytes:
                self.datastore[out].attrs['nbytes'] = nbytes
                logging.info('Saved %s in %s', humansize(nbytes), out)
            else:  # remove empty outputs
                del self.datastore[out]

        if self.oqparam.specific_assets:
            self.build_specific_loss_curves(
                self.datastore['specific-losses-rlzs'])

        rlzs = self.rlzs_assoc.realizations
        if len(rlzs) > 1:
            self.compute_store_stats(rlzs, '')  # generic
            self.compute_store_stats(rlzs, '_specific')

        # The following is commented on purpose:
        # if (self.oqparam.conditional_loss_poes and
        #         'rcurves-rlzs' in self.datastore):
        #     self.build_loss_maps()

    def clean_up(self):
        """
        Final checks and cleanup
        """
        if (self.oqparam.ground_motion_fields and
                'gmf_by_trt_gsim' not in self.datastore):
            logging.warn(
                'Even if the flag `ground_motion_fields` was set the GMFs '
                'were not saved.\nYou should use the event_based hazard '
                'calculator to do that, not the risk one')
        super(EventBasedRiskCalculator, self).clean_up()

    def build_specific_loss_curves(self, group, kind='loss'):
        ses_ratio = self.oqparam.ses_ratio
        assetcol = self.assetcol[self.spec_indices]
        for loss_type, builder in zip(group, self.riskmodel.curve_builders):
            for rlz, dset in group[loss_type].items():
                losses_by_aid = collections.defaultdict(list)
                for ela in dset.value:
                    losses_by_aid[ela['ass_id']].append(ela[kind])
                curves = builder.build_loss_curves(
                    assetcol, losses_by_aid, ses_ratio)
                key = 'specific-loss_curves-rlzs/%s/%s' % (loss_type, rlz)
                self.datastore[key] = curves

    def build_loss_maps(self):
        """
        Build loss maps from the loss curves
        """
        oq = self.oqparam
        for loss_type, group in self.datastore['rcurves-rlzs'].items():
            asset_values = self.assetcol[loss_type]
            ratios = group.attrs['loss_ratios']
            for rlz, poe_matrix in group.items():
                maps = scientific.calc_loss_maps(
                    oq.conditional_loss_poes, asset_values, ratios, poe_matrix)
                key = 'lmaps-rlzs/%s/%s' % (loss_type, rlz)
                self.datastore[key] = maps

    # ################### methods to compute statistics  #################### #

    def build_stats(self, builder):
        """
        Compute all statistics for all assets starting from the
        stored loss curves. Yield a statistical output object for each
        loss type.
        """
        if 'rcurves-rlzs' not in self.datastore:
            return []
        stats = []
        # NB: should we encounter memory issues in the future, the easy
        # solution is to split the assets in blocks and perform
        # the computation one block at the time
        assets = self.assetcol['asset_ref']
        rlzs = self.rlzs_assoc.realizations
        for loss_type in self.riskmodel.loss_types:
            group = self.datastore['rcurves-rlzs/%s' % loss_type]
            asset_values = self.assetcol[loss_type]
            data = []
            for rlz, dataset in zip(rlzs, group.values()):
                dkey = 'avg_losses-rlzs/%s/%s' % (loss_type, rlz.uid)
                average_losses = self.datastore[dkey].value
                ratios = group.attrs['loss_ratios']
                lcs = []
                for avalue, poes in zip(asset_values, dataset['poes']):
                    lcs.append((avalue * ratios, poes))
                losses_poes = numpy.array(lcs)  # -> shape (N, 2, C)
                out = scientific.Output(
                    assets, loss_type, rlz.ordinal, rlz.weight,
                    loss_curves=losses_poes, insured_curves=None,
                    average_losses=average_losses[:, 0],
                    average_insured_losses=average_losses[:, 1])
                data.append(out)
            stats.append(builder.build(data))
        return stats

    # TODO: add a direct test
    def build_specific_stats(self, builder):
        """
        Compute all statistics for the specified assets starting from the
        stored loss curves. Yield a statistical output object for each
        loss type.
        """
        if not self.oqparam.specific_assets:
            return []

        specific_assets = set(self.oqparam.specific_assets)
        assetcol = self.assetcol
        specific_ids = []
        for i, a in enumerate(self.assetcol):
            if a['asset_ref'] in specific_assets:
                specific_ids.append(i)

        assets = assetcol['asset_ref']
        rlzs = self.rlzs_assoc.realizations
        stats = []
        for loss_type in self.riskmodel.loss_types:
            group = self.datastore['/specific-loss_curves-rlzs/%s' % loss_type]
            data = []
            for rlz, dataset in zip(rlzs, group.values()):
                dkey = 'avg_losses-rlzs/%s/%s' % (loss_type, rlz.uid)
                average_losses = self.datastore[dkey][specific_ids]
                lcs = dataset.value
                losses_poes = numpy.array(  # -> shape (N, 2, C)
                    [lcs['losses'], lcs['poes']]).transpose(1, 0, 2)
                out = scientific.Output(
                    assets, loss_type, rlz.ordinal, rlz.weight,
                    loss_curves=losses_poes, insured_curves=None,
                    average_losses=average_losses[:, 0],
                    average_insured_losses=average_losses[:, 1])
                data.append(out)
            stats.append(builder.build(data, prefix='specific-'))
        return stats

    def compute_store_stats(self, rlzs, kind):
        """
        Compute and store the statistical outputs
        """
        oq = self.oqparam
        N = (len(self.oqparam.specific_assets) if kind == '_specific'
             else len(self.assetcol))
        Q = 1 + len(oq.quantile_loss_curves)
        C = oq.loss_curve_resolution  # TODO: could be loss_type-dependent

        loss_curve_dt = numpy.dtype(
            [('losses', (float, C)), ('poes', (float, C)), ('avg', float)])

        if oq.conditional_loss_poes:
            lm_names = _loss_map_names(oq.conditional_loss_poes)
            loss_map_dt = numpy.dtype([(f, float) for f in lm_names])

        loss_curve_stats = numpy.zeros((Q, N), loss_curve_dt)
        ins_curve_stats = numpy.zeros((Q, N), loss_curve_dt)
        if oq.conditional_loss_poes:
            loss_map_stats = numpy.zeros((Q, N), loss_map_dt)

        builder = scientific.StatsBuilder(
            oq.quantile_loss_curves, oq.conditional_loss_poes, [],
            scientific.normalize_curves_eb)

        build_stats = getattr(self, 'build%s_stats' % kind)
        all_stats = build_stats(builder)
        for stat in all_stats:
            # there is one stat for each loss_type
            curves, ins_curves, maps = scientific.get_stat_curves(stat)
            loss_curve_stats[:] = curves
            if oq.insured_losses:
                ins_curve_stats[:] = ins_curves
            if oq.conditional_loss_poes:
                loss_map_stats[:] = maps

            for i, path in enumerate(stat.paths):
                self._store(path % 'loss_curves', loss_curve_stats[i])
                self._store(path % 'ins_curves', ins_curve_stats[i])
                if oq.conditional_loss_poes:
                    self._store(path % 'loss_maps', loss_map_stats[i])

        stats = scientific.SimpleStats(rlzs, oq.quantile_loss_curves)
        stats.compute_and_store('avg_losses', self.datastore)

    def _store(self, path, curves):
        if curves.view(float).sum():
            # there are some nonzero values
            self.datastore[path] = curves


def _loss_map_names(conditional_loss_poes):
    names = []
    for clp in conditional_loss_poes:
        names.append('poe~%s' % clp)
    return names
