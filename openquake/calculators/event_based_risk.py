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
from __future__ import division
import logging
import operator
import itertools
import collections

import numpy

from openquake.baselib.general import AccumDict, humansize
from openquake.calculators import base
from openquake.commonlib import readinput, parallel, datastore
from openquake.risklib import riskinput, scientific
from openquake.commonlib.parallel import apply_reduce

U32 = numpy.uint32
F32 = numpy.float32


@parallel.litetask
def build_agg_curve(r_data, insured_losses, ses_ratio, curve_resolution,
                    monitor):
    """
    Build the aggregate loss curve in parallel for each loss type
    and realization pair.

    :param r_data:
        a list of pairs `(r, data)` where `r` is a realization index and `data`
        is an array of pairs `(rupture_id, loss)` where loss is an array of
        shape L, 2
    :param insured_losses:
        job.ini configuration parameter
    :param ses_ratio:
        a ratio obtained from ses_per_logic_tree_path
    :param curve_resolution:
        the number of discretization steps for the loss curve
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary (r, l, i) -> (losses, poes, avg)
    """
    result = {}
    for r, data in r_data:
        if len(data) == 0:  # realization with no losses
            continue
        E, L = data['loss'].shape[:2]
        for l in range(L):
            losses, poes = scientific.event_based(
                data['loss'][:, l, 0], ses_ratio, curve_resolution)
            avg = scientific.average_loss((losses, poes))
            result[l, r, 'losses'] = losses
            result[l, r, 'poes'] = poes
            result[l, r, 'avg'] = avg
            if insured_losses:
                losses_ins, poes_ins = scientific.event_based(
                    data['loss'][:, l, 1], ses_ratio, curve_resolution)
                avg_ins = scientific.average_loss((losses_ins, poes_ins))
                result[l, r, 'losses_ins'] = losses_ins
                result[l, r, 'poes_ins'] = poes_ins
                result[l, r, 'avg_ins'] = avg_ins
    return result


def square(L, R, factory):
    """
    :param L: the number of loss types
    :param R: the number of realizations
    :param factory: thunk used to initialize the elements
    :returns: a numpy matrix of shape (L, R)
    """
    losses = numpy.zeros((L, R), object)
    for l in range(L):
        for r in range(R):
            losses[l, r] = factory()
    return losses


def _old_loss_curves(asset_values, rcurves, ratios):
    # build loss curves in the old format (i.e. (losses, poes)) from
    # loss curves in the new format (i.e. poes).
    # shape (N, 2, C)
    return numpy.array([(avalue * ratios, poes)
                        for avalue, poes in zip(asset_values, rcurves)])


@parallel.litetask
def event_based_risk(riskinputs, riskmodel, rlzs_assoc, assets_by_site,
                     monitor):
    """
    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
    :param assets_by_site:
        a representation of the exposure
    :param monitor:
        :class:`openquake.baselib.performance.PerformanceMonitor` instance
    :returns:
        a dictionary of numpy arrays of shape (L, R)
    """
    lti = riskmodel.lti  # loss type -> index
    L, R = len(lti), len(rlzs_assoc.realizations)
    ela_dt = numpy.dtype([('rup_id', U32), ('ass_id', U32),
                          ('loss', (F32, (L, 2)))])
    elt_dt = numpy.dtype([('rup_id', U32), ('loss', (F32, (L, 2)))])

    def zeroN2():
        return numpy.zeros((monitor.num_assets, 2))
    result = dict(RC=square(L, R, list), IC=square(L, R, list))
    if monitor.avg_losses:
        result['AVGLOSS'] = square(L, R, zeroN2)
    ass_losses = []
    for out_by_rlz in riskmodel.gen_outputs(
            riskinputs, rlzs_assoc, monitor, assets_by_site):
        for out in out_by_rlz:
            l = lti[out.loss_type]
            r = out.hid
            asset_ids = [a.idx for a in out.assets]

            # aggregate losses per rupture
            for rup_id, all_losses, ins_losses in zip(
                    out.tags, out.event_loss_per_asset,
                    out.insured_loss_per_asset):
                for aid, groundloss, insuredloss in zip(
                        asset_ids, all_losses, ins_losses):
                    if groundloss > 0:
                        loss2 = numpy.array([groundloss, insuredloss])
                        ass_losses.append((r, rup_id, aid, l, loss2))

            # dictionaries asset_idx -> array of counts
            if riskmodel.curve_builders[l].user_provided:
                result['RC'][l, r].append(dict(
                    zip(asset_ids, out.counts_matrix)))
                if out.insured_counts_matrix.sum():
                    result['IC'][l, r].append(dict(
                        zip(asset_ids, out.insured_counts_matrix)))

            # average losses
            if monitor.avg_losses:
                arr = numpy.zeros((monitor.num_assets, 2))
                for aid, avgloss, ins_avgloss in zip(
                        asset_ids, out.average_losses,
                        out.average_insured_losses):
                    # NB: here I cannot use numpy.float32, because the sum of
                    # numpy.float32 numbers is noncommutative!
                    # the net effect is that the final loss is affected by
                    # the order in which the tasks are run, which is random
                    # i.e. at each run one may get different results!!
                    arr[aid] = [avgloss, ins_avgloss]
                result['AVGLOSS'][l, r] += arr

    ass_losses.sort()

    # ASSLOSS
    items = [[] for _ in range(R)]
    for (r, rid, aid), group in itertools.groupby(
            ass_losses, operator.itemgetter(0, 1, 2)):
        loss = numpy.zeros((L, 2), F32)
        for _r, _rid, _aid, l, loss2 in group:
            loss[l] = loss2
        items[r].append((rid, aid, loss))
    for r in range(R):
        items[r] = numpy.array(items[r], ela_dt)
    result['ASSLOSS'] = items

    # AGGLOSS
    items = [[] for _ in range(R)]
    for (r, rid), group in itertools.groupby(
            ass_losses, operator.itemgetter(0, 1)):
        loss = numpy.zeros((L, 2), F32)
        for _r, _rid, _aid, l, loss2 in group:
            loss[l] += loss2
        items[r].append((rid, loss))
    for r in range(R):
        items[r] = numpy.array(items[r], elt_dt)
    result['AGGLOSS'] = items

    for (l, r), lst in numpy.ndenumerate(result['RC']):
        result['RC'][l, r] = sum(lst, AccumDict())
    for (l, r), lst in numpy.ndenumerate(result['IC']):
        result['IC'][l, r] = sum(lst, AccumDict())

    return result


class FakeMatrix(object):
    """
    A fake epsilon matrix, to be used when the coefficients are all zeros,
    so the epsilons are ignored.
    """
    def __init__(self, n, e):
        self.shape = (n, e)

    def __getitem__(self, sliceobj):
        if isinstance(sliceobj, int):
            e = self.shape[1]
            return numpy.zeros(e, F32)
        elif len(sliceobj) == 2:
            n = self.shape[0]
            s1, s2 = sliceobj
            size2 = s2.stop - s2.start
            return self.__class__(n, size2)
        else:
            raise ValueError('Not a valid slice: %r' % sliceobj)


@base.calculators.add('event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the event loss table and
    fixed ratios loss curves.
    """
    pre_calculator = 'event_based'
    core_func = event_based_risk

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
        correl_model = readinput.get_correl_model(oq)
        gsims_by_col = self.rlzs_assoc.get_gsims_by_col()
        assets_by_site = self.assets_by_site
        # the following is needed to set the asset idx attribute
        self.assetcol = riskinput.build_asset_collection(
            assets_by_site, oq.time_event)

        logging.info('Populating the risk inputs')
        rup_by_tag = sum(self.datastore['sescollection'], AccumDict())
        all_ruptures = [rup_by_tag[tag] for tag in sorted(rup_by_tag)]
        for i, rup in enumerate(all_ruptures):
            rup.ordinal = i
        self.N = len(self.assetcol)
        self.E = len(all_ruptures)
        if not self.riskmodel.covs:
            # do not generate epsilons
            eps = FakeMatrix(self.N, self.E)
        else:
            self.epsilon_matrix = eps = riskinput.make_eps(
                assets_by_site, self.E, oq.master_seed,
                oq.asset_correlation)
            logging.info('Generated %s epsilons', eps.shape)
        self.riskinputs = list(self.riskmodel.build_inputs_from_ruptures(
            self.sitecol.complete, all_ruptures, gsims_by_col,
            oq.truncation_level, correl_model, eps,
            oq.concurrent_tasks or 1))
        logging.info('Built %d risk inputs', len(self.riskinputs))

        # preparing empty datasets
        loss_types = self.riskmodel.loss_types
        self.C = self.oqparam.loss_curve_resolution
        self.L = L = len(loss_types)
        self.R = R = len(self.rlzs_assoc.realizations)
        self.I = self.oqparam.insured_losses

        # ugly: attaching an attribute needed in the task function
        self.monitor.num_assets = self.count_assets()
        self.monitor.avg_losses = self.oqparam.avg_losses
        self.monitor.asset_loss_table = self.oqparam.asset_loss_table

        self.N = N = len(self.assetcol)
        self.E = len(self.datastore['tags'])
        ltypes = self.riskmodel.loss_types

        # average losses, stored in a composite array of shape N, R, 2
        multi_avg_dt = numpy.dtype([(lt, F32) for lt in ltypes])
        self.avg_losses = numpy.zeros((N, R, 2), multi_avg_dt)

        ela_dt = numpy.dtype([('rup_id', U32), ('ass_id', U32),
                              ('loss', (F32, (L, 2)))])
        self.asset_loss_table = [None] * R
        self.agg_loss_table = [None] * R

        self.elt_dt = numpy.dtype([('rup_id', U32), ('loss', (F32, (L, 2)))])
        for rlz in self.rlzs_assoc.realizations:
            self.asset_loss_table[rlz.ordinal] = self.datastore.create_dset(
                'asset_loss_table/%s' % rlz.uid, ela_dt)
            self.agg_loss_table[rlz.ordinal] = self.datastore.create_dset(
                'agg_loss_table/%s' % rlz.uid, self.elt_dt)

    def execute(self):
        """
        Run the event_based_risk calculator and aggregate the results
        """
        self.saved = collections.Counter()  # nbytes per HDF5 key
        self.ass_bytes = 0
        self.agg_bytes = 0
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, self.rlzs_assoc,
             self.assets_by_site, self.monitor.new('task')),
            concurrent_tasks=self.oqparam.concurrent_tasks, agg=self.agg,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('col_id'))

    def agg(self, acc, result):
        """
        Aggregate losses and store them in the datastore.

        :param acc: accumulator dictionary
        :param result: dictionary coming from event_based_risk
        """
        with self.monitor('saving event loss tables', autoflush=True):
            for r, records in enumerate(result.pop('ASSLOSS')):
                self.asset_loss_table[r].extend(records)
                self.ass_bytes += records.nbytes
            for r, records in enumerate(result.pop('AGGLOSS')):
                self.agg_loss_table[r].extend(records)
                self.agg_bytes += records.nbytes
            self.datastore.hdf5.flush()

        return acc + result

    def post_execute(self, result):
        """
        Save the event loss table in the datastore.

        :param result:
            the dictionary returned by the .execute method
        """
        self.datastore['asset_loss_table'].attrs['nbytes'] = self.ass_bytes
        self.datastore['agg_loss_table'].attrs['nbytes'] = self.agg_bytes
        for rlz in self.realizations:
            elt = self.datastore['asset_loss_table/%s' % rlz['uid']]
            alt = self.datastore['agg_loss_table/%s' % rlz['uid']]
            elt.attrs['nonzero_fraction'] = len(elt) / (self.N * self.E)
            alt.attrs['nonzero_fraction'] = len(alt) / self.N

        insured_losses = self.oqparam.insured_losses
        ses_ratio = self.oqparam.ses_ratio
        saved = self.saved
        self.N = N = len(self.assetcol)
        self.R = R = len(self.rlzs_assoc.realizations)
        ltypes = self.riskmodel.loss_types

        self.loss_curve_dt, self.loss_maps_dt = (
            self.riskmodel.build_loss_dtypes(
                self.oqparam.conditional_loss_poes, self.I))

        # loss curves
        multi_lr_dt = numpy.dtype(
            [(ltype, (F32, cbuilder.curve_resolution))
             for ltype, cbuilder in zip(
                ltypes, self.riskmodel.curve_builders)])
        rcurves = numpy.zeros((N, R, 2), multi_lr_dt)

        # AVGLOSS
        if self.oqparam.avg_losses:
            with self.monitor('building avg_losses-rlzs'):
                for (l, r), avgloss in numpy.ndenumerate(
                        result['AVGLOSS']):
                    lt = self.riskmodel.loss_types[l]
                    avg_losses_lt = self.avg_losses[lt]
                    asset_values = self.assetcol[lt]
                    for i, avalue in enumerate(asset_values):
                        avg_losses_lt[i, r] = avgloss[i] * avalue
                self.datastore['avg_losses-rlzs'] = self.avg_losses
                saved['avg_losses-rlzs'] = self.avg_losses.nbytes

        # RC, IC
        if self.oqparam.loss_ratios:
            with self.monitor('building rcurves-rlzs'):
                for (l, r), data in numpy.ndenumerate(result['RC']):
                    cb = self.riskmodel.curve_builders[l]
                    if data and cb.user_provided:
                        # data is a dict asset idx -> counts
                        lt = self.riskmodel.loss_types[l]
                        poes = cb.build_poes(N, [data], ses_ratio)
                        rcurves[lt][:, r, 0] = poes
                        saved['rcurves-rlzs'] += poes.nbytes
                for (l, r), data in numpy.ndenumerate(result['IC']):
                    cb = self.riskmodel.curve_builders[l]
                    if data and cb.user_provided and insured_losses:
                        # data is a dict asset idx -> counts
                        lt = self.riskmodel.loss_types[l]
                        poes = cb.build_poes(N, [data], ses_ratio)
                        rcurves[lt][:, r, 1] = poes
                        saved['rcurves-rlzs'] += poes.nbytes
                self.datastore['rcurves-rlzs'] = rcurves

        oq = self.oqparam
        builder = scientific.StatsBuilder(
            oq.quantile_loss_curves, oq.conditional_loss_poes, [],
            oq.loss_curve_resolution, scientific.normalize_curves_eb)

        # build an aggregate loss curve per realization plus statistics
        with self.monitor('building agg_curve'):
            self.build_agg_curve_and_stats(builder)
        self.datastore.hdf5.flush()

        for out in sorted(saved):
            nbytes = saved[out]
            if nbytes:
                self.datastore[out].attrs['nbytes'] = nbytes
                logging.info('Saved %s in %s', humansize(nbytes), out)

        if self.oqparam.asset_loss_table:
            pass  # TODO: build specific loss curves

        rlzs = self.rlzs_assoc.realizations
        with self.monitor('building loss_maps-rlzs'):
            if (self.oqparam.conditional_loss_poes and
                    'rcurves-rlzs' in self.datastore):
                loss_maps = numpy.zeros((N, R), self.loss_maps_dt)
                rcurves = self.datastore['rcurves-rlzs']
                for cb in self.riskmodel.curve_builders:
                    if cb.user_provided:
                        lm = loss_maps[cb.loss_type]
                        for r, lmaps in cb.build_loss_maps(
                                self.assetcol, rcurves):
                            lm[:, r] = lmaps
                self.datastore['loss_maps-rlzs'] = loss_maps

        if len(rlzs) > 1:
            self.Q1 = len(self.oqparam.quantile_loss_curves) + 1
            with self.monitor('computing stats'):
                self.compute_store_stats(rlzs, builder)

    def build_agg_curve_and_stats(self, builder):
        """
        Build a single loss curve per realization. It is NOT obtained
        by aggregating the loss curves; instead, it is obtained without
        generating the loss curves, directly from the the aggregate losses.
        """
        oq = self.oqparam
        C = oq.loss_curve_resolution
        loss_curve_dt, _ = self.riskmodel.build_all_loss_dtypes(
            C, oq.conditional_loss_poes, oq.insured_losses)
        lts = self.riskmodel.loss_types
        r_data = [(r, dset.value) for r, dset in enumerate(
            self.datastore['agg_loss_table'].values())]
        ses_ratio = self.oqparam.ses_ratio
        result = parallel.apply_reduce(
            build_agg_curve, (r_data, self.I, ses_ratio, C, self.monitor('')),
            concurrent_tasks=self.oqparam.concurrent_tasks)
        agg_curve = numpy.zeros(self.R, loss_curve_dt)
        for l, r, name in result:
            agg_curve[lts[l]][name][r] = result[l, r, name]
        self.datastore['agg_curve-rlzs'] = agg_curve
        self.saved['agg_curve-rlzs'] = agg_curve.nbytes

        if self.R > 1:
            self.build_agg_curve_stats(builder, loss_curve_dt)

    # ################### methods to compute statistics  #################### #

    def _collect_all_data(self):
        # return a list of list of outputs
        if 'rcurves-rlzs' not in self.datastore:
            return []
        all_data = []
        assets = self.assetcol['asset_ref']
        rlzs = self.rlzs_assoc.realizations
        insured = self.oqparam.insured_losses
        if self.oqparam.avg_losses:
            avg_losses = self.datastore['avg_losses-rlzs'].value
        else:
            avg_losses = self.avg_losses
        r_curves = self.datastore['rcurves-rlzs'].value
        for loss_type, cbuilder in zip(
                self.riskmodel.loss_types, self.riskmodel.curve_builders):
            rcurves = r_curves[loss_type]
            asset_values = self.assetcol[loss_type]
            data = []
            avglosses = avg_losses[loss_type]
            for rlz in rlzs:
                average_losses = avglosses[:, rlz.ordinal, 0]
                average_insured_losses = (avglosses[:, rlz.ordinal, 1]
                                          if insured else None)
                loss_curves = _old_loss_curves(
                    asset_values, rcurves[:, rlz.ordinal, 0], cbuilder.ratios)
                insured_curves = _old_loss_curves(
                    asset_values, rcurves[:, rlz.ordinal, 1],
                    cbuilder.ratios) if insured else None
                out = scientific.Output(
                    assets, loss_type, rlz.ordinal, rlz.weight,
                    loss_curves=loss_curves,
                    insured_curves=insured_curves,
                    average_losses=average_losses,
                    average_insured_losses=average_insured_losses)
                data.append(out)
            all_data.append(data)
        return all_data

    # NB: the HDF5 structure is of kind <output>-stats/structural/mean, ...
    # and must be so for the loss curves, since different loss_types may have
    # a different discretization. This is not needed for the loss maps, but it
    # is done anyway for consistency, also because in the future we could
    # specify different conditional loss poes depending on the loss type
    def compute_store_stats(self, rlzs, builder):
        """
        Compute and store the statistical outputs.
        :param rlzs: list of realizations
        """
        oq = self.oqparam
        ltypes = self.riskmodel.loss_types
        all_stats = map(builder.build, self._collect_all_data())
        if not all_stats:
            return
        loss_curves = numpy.zeros((self.Q1, self.N), self.loss_curve_dt)
        loss_maps = numpy.zeros((self.Q1, self.N), self.loss_maps_dt)
        for stats in all_stats:
            # there is one stat for each loss_type
            cb = self.riskmodel.curve_builders[ltypes.index(stats.loss_type)]
            if not cb.user_provided:
                continue
            sb = scientific.StatsBuilder(
                oq.quantile_loss_curves, oq.conditional_loss_poes, [],
                len(cb.ratios), scientific.normalize_curves_eb,
                oq.insured_losses)
            curves, maps = sb.get_curves_maps(stats)  # matrices (Q1, N)
            lc = loss_curves[cb.loss_type]
            lm = loss_maps[cb.loss_type]
            for i, statname in enumerate(sb.mean_quantiles):
                for name in curves.dtype.names:
                    lc[name][i] = curves[name][i]
                for name in maps.dtype.names:
                    lm[name][i] = maps[name][i]
        self.datastore['loss_curves-stats'] = loss_curves
        if oq.conditional_loss_poes:
            self.datastore['loss_maps-stats'] = loss_maps

        if oq.avg_losses:  # stats for avg_losses
            stats = scientific.SimpleStats(rlzs, oq.quantile_loss_curves)
            stats.compute('avg_losses-rlzs', self.datastore)

        self.datastore.hdf5.flush()

    def build_agg_curve_stats(self, builder, loss_curve_dt):
        """
        Build and save `agg_curve-stats` in the HDF5 file.

        :param builder:
            :class:`openquake.risklib.scientific.StatsBuilder` instance
        """
        rlzs = self.datastore['rlzs_assoc'].realizations
        agg_curve = self.datastore['agg_curve-rlzs']
        Q1 = len(builder.mean_quantiles)
        agg_curve_stats = numpy.zeros(Q1, loss_curve_dt)
        for l, loss_type in enumerate(self.riskmodel.loss_types):
            agg_curve_lt = agg_curve[loss_type]
            outputs = []
            for rlz in rlzs:
                curve = agg_curve_lt[rlz.ordinal]
                average_loss = curve['avg']
                loss_curve = (curve['losses'], curve['poes'])
                if self.oqparam.insured_losses:
                    average_insured_loss = curve['avg_ins']
                    insured_curves = [(curve['losses_ins'], curve['poes_ins'])]
                else:
                    average_insured_loss = None
                    insured_curves = None
                out = scientific.Output(
                    [None], loss_type, rlz.ordinal, rlz.weight,
                    loss_curves=[loss_curve],
                    insured_curves=insured_curves,
                    average_losses=[average_loss],
                    average_insured_losses=[average_insured_loss])
                outputs.append(out)
            stats = builder.build(outputs)
            curves, _maps = builder.get_curves_maps(stats)  # shape (Q1, 1)
            acs = agg_curve_stats[loss_type]
            for i, statname in enumerate(builder.mean_quantiles):
                for name in acs.dtype.names:
                    acs[name][i] = curves[name][i]

        # saving agg_curve_stats
        self.datastore['agg_curve-stats'] = agg_curve_stats
        self.datastore['agg_curve-stats'].attrs['nbytes'] = (
            agg_curve_stats.nbytes)
