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

U32 = numpy.uint32
F32 = numpy.float32


@parallel.litetask
def build_agg_curve(lr_list, insured_losses, ses_ratio, C, monitor):
    """
    Build the aggregate loss curve in parallel, by distributing on the pairs
    (l, r) i.e. loss types and realizations.

    :returns: a dictionary (r, l, i) -> (losses, poes, avg)
    """
    result = {}
    for l, r, data in lr_list:
        if len(data) == 0:  # realization with no losses
            continue
        for i in range(insured_losses + 1):  # insured_losses
            the_losses = numpy.array(
                [loss[i] for _rupid, loss in data], F32)
            losses, poes = scientific.event_based(
                the_losses, ses_ratio, C)
            avg = scientific.average_loss((losses, poes))
            result[l, r, i] = (losses, poes, avg)
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


@parallel.litetask
def event_based_risk(riskinputs, riskmodel, rlzs_assoc, assets_by_site,
                     eps, specific_assets, monitor):
    """
    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
    :param assets_by_site:
        a representation of the exposure
    :param eps:
        a matrix of shape (N, E) with N=#assets and E=#ruptures
    :param specific_assets:
        .ini file parameter
    :param monitor:
        :class:`openquake.baselib.performance.PerformanceMonitor` instance
    :returns:
        a dictionary of numpy arrays of shape (L, R)
    """
    lti = riskmodel.lti  # loss type -> index
    L, R = len(lti), len(rlzs_assoc.realizations)

    def zeroN2():
        return numpy.zeros((monitor.num_assets, 2))
    result = dict(AGGLOSS=square(L, R, list),
                  SPECLOSS=square(L, R, list),
                  RC=square(L, R, list),
                  IC=square(L, R, list))
    if monitor.avg_losses:
        result['AVGLOSS'] = square(L, R, zeroN2)
    for out_by_rlz in riskmodel.gen_outputs(
            riskinputs, rlzs_assoc, monitor, assets_by_site, eps):
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
                                result['SPECLOSS'][l, out.hid].append(
                                    (rup_id, aid, numpy.array([sloss, iloss])))

            # collect aggregate losses
            agg_losses = out.event_loss_per_asset.sum(axis=1)
            agg_ins_losses = out.insured_loss_per_asset.sum(axis=1)
            for rup_id, loss, ins_loss in zip(
                    rup_ids, agg_losses, agg_ins_losses):
                if loss > 0:
                    result['AGGLOSS'][l, out.hid].append(
                        (rup_id, numpy.array([loss, ins_loss])))

            # dictionaries asset_idx -> array of counts
            if riskmodel.curve_builders[l].user_provided:
                result['RC'][l, out.hid].append(dict(
                    zip(asset_ids, out.counts_matrix)))
                if out.insured_counts_matrix.sum():
                    result['IC'][l, out.hid].append(dict(
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
                result['AVGLOSS'][l, out.hid] += arr

    for (l, r), lst in numpy.ndenumerate(result['AGGLOSS']):
        # aggregate the losses corresponding to the same rupture
        acc = collections.defaultdict(float)
        for rupt, loss in lst:
            acc[rupt] += loss
        result['AGGLOSS'][l, r] = acc.items()
    for (l, r), lst in numpy.ndenumerate(result['RC']):
        result['RC'][l, r] = sum(lst, AccumDict())
    for (l, r), lst in numpy.ndenumerate(result['IC']):
        result['IC'][l, r] = sum(lst, AccumDict())

    return result


@base.calculators.add('event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the event loss table and
    fixed ratios loss curves.
    """
    pre_calculator = 'event_based'
    core_func = event_based_risk

    epsilon_matrix = datastore.persistent_attribute('epsilon_matrix')
    spec_indices = datastore.persistent_attribute('spec_indices')
    is_stochastic = True

    outs = collections.OrderedDict(
        [('AVGLOSS', 'avg_losses-rlzs'),
         ('AGGLOSS', 'agg_losses-rlzs'),
         ('SPECLOSS', 'specific-losses-rlzs'),
         ('RC', 'rcurves-rlzs'),
         ('IC', 'icurves-rlzs')])

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
        self.epsilon_matrix = eps = riskinput.make_eps(
            assets_by_site, num_samples, oq.master_seed, oq.asset_correlation)
        logging.info('Generated %d epsilons', num_samples * len(eps))
        self.riskinputs = list(self.riskmodel.build_inputs_from_ruptures(
            self.sitecol.complete, all_ruptures, gsims_by_col,
            oq.truncation_level, correl_model, eps,
            oq.concurrent_tasks or 1))
        logging.info('Built %d risk inputs', len(self.riskinputs))

        # preparing empty datasets
        loss_types = self.riskmodel.loss_types
        self.L = len(loss_types)
        self.R = len(self.rlzs_assoc.realizations)
        self.elt_dt = numpy.dtype([('rup_id', U32), ('loss', (F32, 2))])
        self.ela_dt = numpy.dtype([('rup_id', U32), ('ass_id', U32),
                                   ('loss', (F32, 2))])

        self.datastore.hdf5.create_group(self.outs['AGGLOSS'])
        self.datastore.hdf5.create_group(self.outs['SPECLOSS'])
        self.dsets = dict(AGGLOSS=numpy.zeros((self.L, self.R), object),
                          SPECLOSS=numpy.zeros((self.L, self.R), object))
        for l, loss_type in enumerate(loss_types):
            for r, rlz in enumerate(self.rlzs_assoc.realizations):
                key = self.outs['AGGLOSS'] + '/%s/%s' % (loss_type, rlz.uid)
                self.dsets['AGGLOSS'][l, r] = self.datastore.create_dset(
                    key, self.elt_dt)
                key = self.outs['SPECLOSS'] + '/%s/%s' % (loss_type, rlz.uid)
                self.dsets['SPECLOSS'][l, r] = self.datastore.create_dset(
                    key, self.ela_dt)

        # ugly: attaching an attribute needed in the task function
        self.monitor.num_assets = self.count_assets()
        self.monitor.avg_losses = self.oqparam.avg_losses

    def execute(self):
        """
        Run the event_based_risk calculator and aggregate the results
        """
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, self.rlzs_assoc,
             self.assets_by_site, self.epsilon_matrix,
             self.oqparam.specific_assets, self.monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('col_id'))

    def post_execute(self, result):
        """
        Save the event loss table in the datastore.

        :param result:
            a numpy array of shape (O, L, R) containing lists of arrays
        """
        insured_losses = self.oqparam.insured_losses
        ses_ratio = self.oqparam.ses_ratio
        saved = collections.Counter()  # nbytes per HDF5 key
        N = len(self.assetcol)
        R = len(self.rlzs_assoc.realizations)
        ltypes = self.riskmodel.loss_types

        # average losses
        multi_avg_dt = numpy.dtype([(lt, (F32, 2)) for lt in ltypes])
        self.avg_losses = numpy.zeros((N, R), multi_avg_dt)

        # loss curves
        multi_lr_dt = numpy.dtype(
            [(ltype, (F32, cbuilder.curve_resolution))
             for ltype, cbuilder in zip(
                ltypes, self.riskmodel.curve_builders)])
        rcurves = numpy.zeros((N, R), multi_lr_dt)
        if insured_losses:
            icurves = numpy.zeros((N, R), multi_lr_dt)
        with self.monitor('saving risk outputs',
                          autoflush=True, measuremem=True) as mon:

            # AVGLOSS
            if self.oqparam.avg_losses:
                with mon('building avg_losses-rlzs'):
                    for (l, r), avgloss in numpy.ndenumerate(
                            result['AVGLOSS']):
                        lt = self.riskmodel.loss_types[l]
                        avg_losses_lt = self.avg_losses[lt]
                        asset_values = self.assetcol[lt]
                        for i, avalue in enumerate(asset_values):
                            avg_losses_lt[i, r] = tuple(avgloss[i] * avalue)
                    self.datastore['avg_losses-rlzs'] = self.avg_losses
                    saved['avg_losses-rlzs'] = self.avg_losses.nbytes

            # AGGLOSS
            with mon('building agg_losses-rlzs'):
                for (l, r), data in numpy.ndenumerate(result['AGGLOSS']):
                    if data:  # # data is a list of arrays
                        losses = numpy.array(data, self.elt_dt)
                        self.dsets['AGGLOSS'][l, r].extend(losses)
                        saved['agg_losses-rlzs'] += losses.nbytes

            # SPECLOSS
            with mon('building specific-losses-rlzs'):
                for (l, r), data in numpy.ndenumerate(result['SPECLOSS']):
                    if data:  # # data is a list of arrays
                        losses = numpy.array(data, self.ela_dt)
                        self.dsets['SPECLOSS'][l, r].extend(losses)
                        saved['specific-losses-rlzs'] += losses.nbytes

            # RC
            with mon('building rcurves-rlzs'):
                for (l, r), data in numpy.ndenumerate(result['RC']):
                    cb = self.riskmodel.curve_builders[l]
                    if data and cb.user_provided:
                        # data is a dict asset idx -> counts
                        lt = self.riskmodel.loss_types[l]
                        poes = cb.build_poes(N, [data], ses_ratio)
                        rcurves[lt][:, r] = poes
                        saved['rcurves-rlzs'] += poes.nbytes
                self.datastore['rcurves-rlzs'] = rcurves

            # IC
            with mon('building icurves-rlzs'):
                for (l, r), data in numpy.ndenumerate(result['IC']):
                    cb = self.riskmodel.curve_builders[l]
                    if data and cb.user_provided and insured_losses:
                        # data is a dict asset idx -> counts
                        lt = self.riskmodel.loss_types[l]
                        poes = cb.build_poes(N, [data], ses_ratio)
                        icurves[lt][:, r] = poes
                        saved['rcurves-rlzs'] += poes.nbytes
                if insured_losses:
                    self.datastore['icurves-rlzs'] = icurves

            # build an aggregate loss curve per realization
            with mon('building agg_curve-rlzs'):
                self.build_agg_curve(saved)

            self.datastore.hdf5.flush()
            self.dsets.clear()

        for out in sorted(saved):
            nbytes = saved[out]
            if nbytes:
                self.datastore[out].attrs['nbytes'] = nbytes
                logging.info('Saved %s in %s', humansize(nbytes), out)

        if self.oqparam.specific_assets:
            with mon('building specific loss curves'):
                self.build_specific_loss_curves(
                    self.datastore['specific-losses-rlzs'])
                # TODO: add insured specific loss curves

        rlzs = self.rlzs_assoc.realizations
        if len(rlzs) > 1:
            with mon('computing stats'):
                self.compute_store_stats(rlzs, '')  # generic
                self.compute_store_stats(rlzs, '_specific')

        with mon('building rmaps-rlzs'):
            if (self.oqparam.conditional_loss_poes and
                    'rcurves-rlzs' in self.datastore):
                self.build_loss_maps('rcurves-rlzs', 'rmaps-rlzs')
            if (self.oqparam.conditional_loss_poes and
                    'icurves-rlzs' in self.datastore):
                self.build_loss_maps('icurves-rlzs', 'imaps-rlzs')

    def build_specific_loss_curves(self, group):
        """
        Build loss curves for specific assets
        """
        ses_ratio = self.oqparam.ses_ratio
        assetcol = self.assetcol[self.spec_indices]
        for cb in self.riskmodel.curve_builders:
            for rlz, dset in group[cb.loss_type].items():
                losses_by_aid = collections.defaultdict(list)
                for ela in dset.value:
                    losses_by_aid[ela['ass_id']].append(ela['loss'][0])
                curves = cb.build_loss_curves(
                    assetcol, losses_by_aid, ses_ratio)
                key = 'specific-loss_curves-rlzs/%s/%s' % (cb.loss_type, rlz)
                self.datastore[key] = curves

    def build_loss_maps(self, curves_key, maps_key):
        """
        Build loss maps from the loss curves
        """
        oq = self.oqparam
        rlzs = self.datastore['rlzs_assoc'].realizations
        curves = self.datastore[curves_key].value
        N = len(self.assetcol)
        R = len(rlzs)
        P = len(oq.conditional_loss_poes)
        loss_map_dt = numpy.dtype(
            [(lt, (F32, P)) for lt in self.riskmodel.loss_types])
        maps = numpy.zeros((N, R), loss_map_dt)
        for cb in self.riskmodel.curve_builders:
            asset_values = self.assetcol[cb.loss_type]
            curves_lt = curves[cb.loss_type]
            maps_lt = maps[cb.loss_type]
            for rlz in rlzs:
                loss_maps = scientific.calc_loss_maps(
                    oq.conditional_loss_poes, asset_values, cb.ratios,
                    curves_lt[:, rlz.ordinal])
                for aid in range(N):
                    # NB: it does not work without the loop, there is a
                    # ValueError:could not broadcast input array from shape
                    # (N,1) into shape (N)
                    maps_lt[aid, rlz.ordinal] = loss_maps[aid]
        self.datastore[maps_key] = maps

    def build_agg_curve(self, saved):
        """
        Build a single loss curve per realization. It is NOT obtained
        by aggregating the loss curves; instead, it is obtained without
        generating the loss curves, directly from the the aggregate losses.
        """
        ltypes = self.riskmodel.loss_types
        C = self.oqparam.loss_curve_resolution
        I = self.oqparam.insured_losses
        rlzs = self.datastore['rlzs_assoc'].realizations
        agglosses = self.datastore['agg_losses-rlzs']
        R = len(rlzs)
        ses_ratio = self.oqparam.ses_ratio
        loss_curve_dt = numpy.dtype([
            ('losses', (F32, C)), ('poes', (F32, C)), ('avg', F32)])
        lr_list = [(l, r.ordinal, agglosses[l][r.uid].value)
                   for l in ltypes for r in rlzs]
        result = parallel.apply_reduce(
            build_agg_curve, (lr_list, I, ses_ratio, C, self.monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks)
        for loss_type in ltypes:
            agg_curve = numpy.empty((R, 2), loss_curve_dt)
            for field in loss_curve_dt.fields:  # loop needed for Ubuntu 12.04
                agg_curve[field].fill(numpy.nan)
            for l, r, i in result:
                if l == loss_type:
                    agg_curve[r, i] = result[l, r, i]
            outkey = 'agg_curve-rlzs/' + loss_type
            self.datastore[outkey] = agg_curve
            saved[outkey] = agg_curve.nbytes

    # ################### methods to compute statistics  #################### #

    def _collect_all_data(self):
        # return a list of list of outputs
        if 'rcurves-rlzs' not in self.datastore:
            return []
        all_data = []
        assets = self.assetcol['asset_ref']
        rlzs = self.rlzs_assoc.realizations
        if self.oqparam.avg_losses:
            avg_losses = self.datastore['avg_losses-rlzs'].value
        else:
            avg_losses = self.avg_losses
        r_curves = self.datastore['rcurves-rlzs'].value
        if self.oqparam.insured_losses:
            i_curves = self.datastore['icurves-rlzs'].value
        else:
            i_curves = []
        for loss_type, cbuilder in zip(
                self.riskmodel.loss_types, self.riskmodel.curve_builders):
            rcurves = r_curves[loss_type]
            asset_values = self.assetcol[loss_type]
            data = []
            avglosses = avg_losses[loss_type]
            for rlz in rlzs:
                average_losses = avglosses[:, rlz.ordinal, 0]
                average_insured_losses = avglosses[:, rlz.ordinal, 1]
                loss_curves = old_loss_curves(
                    asset_values, rcurves, rlz.ordinal, cbuilder.ratios)
                insured_curves = old_loss_curves(
                    asset_values, i_curves[loss_type], rlz.ordinal,
                    cbuilder.ratios) if len(i_curves) else None
                out = scientific.Output(
                    assets, loss_type, rlz.ordinal, rlz.weight,
                    loss_curves=loss_curves,
                    insured_curves=insured_curves,
                    average_losses=average_losses,
                    average_insured_losses=average_insured_losses)
                data.append(out)
            all_data.append(data)
        return all_data

    def _collect_specific_data(self):
        # return a list of list of outputs
        if not self.oqparam.specific_assets:
            return []

        specific_assets = set(self.oqparam.specific_assets)
        assetcol = self.assetcol
        specific_ids = []
        for i, a in enumerate(assetcol):
            if a['asset_ref'] in specific_assets:
                specific_ids.append(i)

        assets = assetcol['asset_ref']
        rlzs = self.rlzs_assoc.realizations
        specific_data = []
        avglosses = self.datastore['avg_losses-rlzs'][specific_ids]
        for loss_type in self.riskmodel.loss_types:
            group = self.datastore['/specific-loss_curves-rlzs/%s' % loss_type]
            data = []
            avglosses_lt = avglosses[loss_type]
            for rlz, dataset in zip(rlzs, group.values()):
                average_losses = avglosses_lt[:, rlz.ordinal]
                lcs = dataset.value
                losses_poes = numpy.array(  # -> shape (N, 2, C)
                    [lcs['losses'], lcs['poes']]).transpose(1, 0, 2)
                out = scientific.Output(
                    assets, loss_type, rlz.ordinal, rlz.weight,
                    loss_curves=losses_poes,
                    insured_curves=None,  # FIXME: why None?
                    average_losses=average_losses[:, 0],
                    average_insured_losses=average_losses[:, 1])
                data.append(out)
            specific_data.append(data)
        return specific_data

    def compute_store_stats(self, rlzs, kind):
        """
        Compute and store the statistical outputs
        """
        oq = self.oqparam
        builder = scientific.StatsBuilder(
            oq.quantile_loss_curves, oq.conditional_loss_poes, [],
            scientific.normalize_curves_eb)

        if kind == '_specific':
            all_stats = [builder.build(data, prefix='specific-')
                         for data in self._collect_specific_data()]
        else:
            all_stats = map(builder.build, self._collect_all_data())
        for stat in all_stats:
            # there is one stat for each loss_type
            curves, ins_curves, maps = scientific.get_stat_curves(stat)
            for i, path in enumerate(stat.paths):
                # there are paths like
                # %s-stats/structural/mean
                # %s-stats/structural/quantile-0.1
                # ...
                self.datastore[path % 'loss_curves'] = curves[i]
                if oq.insured_losses:
                    self.datastore[path % 'ins_curves'] = ins_curves[i]
                if oq.conditional_loss_poes:
                    self.datastore[path % 'loss_maps'] = maps[i]

        if oq.avg_losses:  # stats for avg_losses
            stats = scientific.SimpleStats(rlzs, oq.quantile_loss_curves)
            stats.compute('avg_losses-rlzs', self.datastore)

        self.datastore.hdf5.flush()


def old_loss_curves(asset_values, rcurves, ordinal, ratios):
    """
    Build loss curves in the old format (i.e. (losses, poes)) from
    loss curves in the new format (i.e. poes).
    """
    lcs = []
    for avalue, poes in zip(asset_values, rcurves[:, ordinal]):
        lcs.append((avalue * ratios, poes))
    return numpy.array(lcs)  # -> shape (N, 2, C)
