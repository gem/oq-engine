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
elt_dt = numpy.dtype([('rup_id', U32), ('loss', (F32, 2))])


@parallel.litetask
def build_agg_curve(lr_list, insured_losses, ses_ratio, curve_resolution,
                    monitor):
    """
    Build the aggregate loss curve in parallel for each loss type
    and realization pair.

    :param lr_list:
        a list of triples `(l, r, data)` where `l` is a loss type string,
        `r` as realization index and `data` is an array of pairs
        `(rupture_id, loss)` where loss is an array with two values
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
    for l, r, data in lr_list:
        if len(data) == 0:  # realization with no losses
            continue
        for i in range(insured_losses + 1):  # insured_losses
            the_losses = data[:, i]
            losses, poes = scientific.event_based(
                the_losses, ses_ratio, curve_resolution)
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


def _old_loss_curves(asset_values, rcurves, ratios):
    # build loss curves in the old format (i.e. (losses, poes)) from
    # loss curves in the new format (i.e. poes).
    # shape (N, 2, C)
    return numpy.array([(avalue * ratios, poes)
                        for avalue, poes in zip(asset_values, rcurves)])


@parallel.litetask
def event_based_risk(riskinputs, riskmodel, rlzs_assoc, assets_by_site,
                     eps, monitor):
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
    :param monitor:
        :class:`openquake.baselib.performance.PerformanceMonitor` instance
    :returns:
        a dictionary of numpy arrays of shape (L, R)
    """
    lti = riskmodel.lti  # loss type -> index
    L, R = len(lti), len(rlzs_assoc.realizations)
    ela_dt = numpy.dtype([('rup_id', U32), ('ass_id', U32),
                          ('loss', (F32, (L, R, 2)))])

    def zeroN2():
        return numpy.zeros((monitor.num_assets, 2))
    result = dict(AGGLOSS=square(L, R, list),
                  SPECLOSS=[],
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

            if monitor.asset_loss_table:
                for rup_id, all_losses, ins_losses in zip(
                        rup_ids, out.event_loss_per_asset,
                        out.insured_loss_per_asset):
                    for aid, sloss, iloss in zip(
                            asset_ids, all_losses, ins_losses):
                        if sloss > 0:
                            result['SPECLOSS'].append(
                                (rup_id, aid, (l, out.hid), (sloss, iloss)))

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
        if lst:
            acc = collections.Counter()
            for rupid, loss in lst:
                acc[rupid] += loss
            # h5py wants sorted array indices
            array = numpy.array(sorted(acc.items()), elt_dt)
            result['AGGLOSS'][l, r] = [array]

    if monitor.asset_loss_table:
        items = []
        for (rid, aid), group in itertools.groupby(
                sorted(result['SPECLOSS']), operator.itemgetter(0, 1)):
            array = numpy.zeros((L, R, 2), F32)
            for _rid, _aid, lr, loss in group:
                array[lr] = loss
            items.append((rid, aid, array))
        result['SPECLOSS'] = numpy.array(items, ela_dt)
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
    is_stochastic = True

    outs = collections.OrderedDict(
        [('AVGLOSS', 'avg_losses-rlzs'),
         ('AGGLOSS', 'agg_losses'),
         ('SPECLOSS', 'asset_loss_table'),
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
        self.C = self.oqparam.loss_curve_resolution
        self.L = L = len(loss_types)
        self.R = R = len(self.rlzs_assoc.realizations)
        self.loss_curve_dt = numpy.dtype([
            ('losses', (F32, self.C)), ('poes', (F32, self.C)), ('avg', F32)])

        # ugly: attaching an attribute needed in the task function
        self.monitor.num_assets = self.count_assets()
        self.monitor.avg_losses = self.oqparam.avg_losses
        self.monitor.asset_loss_table = self.oqparam.asset_loss_table

        self.N = N = len(self.assetcol)
        ltypes = self.riskmodel.loss_types

        # average losses, stored in a composite array of shape N, R, 2
        multi_avg_dt = numpy.dtype([(lt, F32) for lt in ltypes])
        self.avg_losses = numpy.zeros((N, R, 2), multi_avg_dt)

        # aggregate losses, stored in a compressed array of shape E, R, 2
        self.E = E = len(self.datastore['tags'])
        self.agg_losses = self.datastore.hdf5.create_dataset(
            'agg_losses', (E, L, R, 2), F32, compression='gzip')
        self.agg_losses.attrs['nbytes'] = 0

        if self.oqparam.asset_loss_table:
            ela_dt = numpy.dtype([('rup_id', U32), ('ass_id', U32),
                                  ('loss', (F32, (L, R, 2)))])
            self.all_losses = self.datastore.create_dset(
                'asset_loss_table', ela_dt, compression='gzip')

    def execute(self):
        """
        Run the event_based_risk calculator and aggregate the results
        """
        self.saved = collections.Counter()  # nbytes per HDF5 key
        self.agg_mon = self.monitor('building agg_losses')
        self.alt_mon = self.monitor('building asset_loss_table')
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, self.rlzs_assoc,
             self.assets_by_site, self.epsilon_matrix, self.monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks, agg=self.agg,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('col_id'))

    def agg(self, acc, result):
        # AGGLOSS
        with self.agg_mon:
            agg_losses = self.agg_losses
            nbytes = 0
            for (l, r), data in numpy.ndenumerate(result['AGGLOSS']):
                # data is a list of arrays of type elt_dt
                for array in data:
                    agg_losses[array['rup_id'], l, r, :] = array['loss']
                    nbytes += array['loss'].nbytes
            self.agg_losses.attrs['nbytes'] += nbytes
            self.datastore.hdf5.flush()

        # SPECLOSS
        if self.oqparam.asset_loss_table:
            with self.alt_mon:
                self.all_losses.extend(result.pop('SPECLOSS'))
                self.datastore.hdf5.flush()

        return acc + result

    def post_execute(self, result):
        """
        Save the event loss table in the datastore.

        :param result:
            a numpy array of shape (O, L, R) containing lists of arrays
        """
        fullsize = numpy.prod(self.agg_losses.shape) * 4  # 32 bit floats
        self.agg_losses.attrs['nonzero_fraction'] = (
            self.agg_losses.attrs['nbytes'] / fullsize)

        if self.oqparam.asset_loss_table:
            dset = self.all_losses.dset
            dset.attrs['nonzero_fraction'] = len(dset) / (self. N * self.E)

        insured_losses = self.oqparam.insured_losses
        ses_ratio = self.oqparam.ses_ratio
        saved = self.saved
        N = len(self.assetcol)
        R = len(self.rlzs_assoc.realizations)
        ltypes = self.riskmodel.loss_types

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

            # build an aggregate loss curve per realization
            with self.monitor('building agg_curve-rlzs'):
                self.build_agg_curve(saved)

            self.datastore.hdf5.flush()

        for out in sorted(saved):
            nbytes = saved[out]
            if nbytes:
                self.datastore[out].attrs['nbytes'] = nbytes
                logging.info('Saved %s in %s', humansize(nbytes), out)

        if self.oqparam.asset_loss_table:
            pass  # TODO: build specific loss curves

        with self.monitor('building loss_maps-rlzs'):
            if (self.oqparam.conditional_loss_poes and
                    'rcurves-rlzs' in self.datastore):
                self.build_loss_maps('rcurves-rlzs', 'loss_maps-rlzs')

        rlzs = self.rlzs_assoc.realizations
        if len(rlzs) > 1:
            with self.monitor('computing stats'):
                self.compute_store_stats(rlzs)

    def build_loss_maps(self, curves_key, maps_key):
        """
        Build loss maps from the risk curves.

        :param curves_key: 'rcurves-rlzs'
        :param maps_key: 'loss_maps-rlzs'
        """
        oq = self.oqparam
        rlzs = self.datastore['rlzs_assoc'].realizations
        curves = self.datastore[curves_key].value
        N = len(self.assetcol)
        I = oq.insured_losses + 1
        poes = ['poe~%s' % clp for clp in oq.conditional_loss_poes]
        loss_map_dt = numpy.dtype([(poe, float) for poe in poes])
        for cb in self.riskmodel.curve_builders:
            if cb.user_provided:  # loss_ratios provided
                asset_values = self.assetcol[cb.loss_type]
                curves_lt = curves[cb.loss_type]
                for rlz in rlzs:
                    loss_map = numpy.zeros((N, 2), loss_map_dt)
                    for ins in range(I):
                        lm = scientific.calc_loss_maps(
                            oq.conditional_loss_poes, asset_values, cb.ratios,
                            curves_lt[:, rlz.ordinal, ins])
                        for i, poes in enumerate(lm):
                            loss_map[i, ins] = tuple(poes)
                    key = '%s/%s/%s' % (maps_key, cb.loss_type, rlz.uid)
                    self.datastore[key] = loss_map

    def build_agg_curve(self, saved):
        """
        Build a single loss curve per realization. It is NOT obtained
        by aggregating the loss curves; instead, it is obtained without
        generating the loss curves, directly from the the aggregate losses.

        :param saved: a Counter {<HDF5 key>: <nbytes>}
        """
        C = self.oqparam.loss_curve_resolution
        I = self.oqparam.insured_losses
        agglosses = self.datastore['agg_losses']
        ses_ratio = self.oqparam.ses_ratio
        lr_list = [(l, r, agglosses[:, l, r, :])
                   for l in range(self.L) for r in range(self.R)]
        result = parallel.apply_reduce(
            build_agg_curve, (lr_list, I, ses_ratio, C, self.monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks)
        agg_curve = numpy.zeros((self.L, self.R, 2), self.loss_curve_dt)
        for l, r, i in result:
            agg_curve[l, r, i] = result[l, r, i]
        self.datastore['agg_curve-rlzs'] = agg_curve
        saved['agg_curve-rlzs'] = agg_curve.nbytes

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
    def compute_store_stats(self, rlzs):
        """
        Compute and store the statistical outputs.
        :param rlzs: list of realizations
        """
        oq = self.oqparam
        ltypes = self.riskmodel.loss_types
        builder = scientific.StatsBuilder(
            oq.quantile_loss_curves, oq.conditional_loss_poes, [],
            oq.loss_curve_resolution, scientific.normalize_curves_eb)
        all_stats = map(builder.build, self._collect_all_data())
        for stats in all_stats:
            # there is one stat for each loss_type
            N = len(stats.assets)
            cb = self.riskmodel.curve_builders[ltypes.index(stats.loss_type)]
            if not cb.user_provided:
                continue
            sb = scientific.StatsBuilder(
                oq.quantile_loss_curves, oq.conditional_loss_poes, [],
                len(cb.ratios), scientific.normalize_curves_eb)
            curves, maps = sb.get_curves_maps(stats)
            for i, path in enumerate(stats.paths):
                # there are paths like
                # %s-stats/structural/mean
                # %s-stats/structural/quantile-0.1
                # ...
                lcs = numpy.zeros((N, 2), sb.loss_curve_dt)
                lms = numpy.zeros((N, 2), sb.loss_map_dt)
                for ins in 0, 1:
                    for aid in range(N):
                        lcs[aid, ins] = curves[ins][i, aid]
                        lms[aid, ins] = maps[ins][i, aid]
                self.datastore[path % 'loss_curves'] = lcs
                if oq.conditional_loss_poes:
                    self.datastore[path % 'loss_maps'] = lms

        self.build_agg_curve_stats(builder)

        if oq.avg_losses:  # stats for avg_losses
            stats = scientific.SimpleStats(rlzs, oq.quantile_loss_curves)
            stats.compute('avg_losses-rlzs', self.datastore)

        self.datastore.hdf5.flush()

    def build_agg_curve_stats(self, builder):
        """
        Build and save `agg_curve-stats` in the HDF5 file.

        :param builder:
            :class:`openquake.risklib.scientific.StatsBuilder` instance
        """
        rlzs = self.datastore['rlzs_assoc'].realizations
        agg_curve = self.datastore['agg_curve-rlzs']
        Q1 = len(builder.quantiles) + 1
        for l, loss_type in enumerate(self.riskmodel.loss_types):
            outputs = []
            for rlz in rlzs:
                curve = agg_curve[l, rlz.ordinal]
                average_loss = curve['avg'][0]
                average_insured_loss = curve['avg'][1]
                loss_curve = (curve['losses'][0],
                              curve['poes'][0])
                if self.oqparam.insured_losses:
                    insured_curves = [(curve['losses'][1], curve['poes'][1])]
                else:
                    insured_curves = None
                out = scientific.Output(
                    [None], loss_type, rlz.ordinal, rlz.weight,
                    loss_curves=[loss_curve],
                    insured_curves=insured_curves,
                    average_losses=[average_loss],
                    average_insured_losses=[average_insured_loss])
                outputs.append(out)
            stats = builder.build(outputs)
            curves, _maps = builder.get_curves_maps(stats)
            # arrays of shape (2, Q1, 1)
            agg_curve_stats = numpy.zeros((Q1, 2), self.loss_curve_dt)
            for name in self.loss_curve_dt.names:
                agg_curve_stats[name][:, 0] = curves[0][name][:, 0]
                if self.oqparam.insured_losses:
                    agg_curve_stats[name][:, 1] = curves[1][name][:, 0]

            for statname in builder.mean_quantiles:
                self.datastore['agg_curve-stats/' + statname] = agg_curve_stats
                self.datastore['agg_curve-stats/' + statname]. \
                    attrs['nbytes'] = agg_curve_stats.nbytes
