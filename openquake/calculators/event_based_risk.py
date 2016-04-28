# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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

from __future__ import division
import logging
import operator
import itertools
import collections

import numpy

from openquake.baselib.python3compat import zip
from openquake.baselib.general import AccumDict, humansize
from openquake.calculators import base, event_based
from openquake.commonlib import readinput, parallel
from openquake.risklib import riskinput, scientific
from openquake.commonlib.parallel import starmap

U32 = numpy.uint32
F32 = numpy.float32


def build_el_dtypes(insured_losses):
    """
    :param bool insured_losses:
        job.ini configuration parameter
    :returns:
        ela_dt and elt_dt i.e. the data types for event loss assets and
        event loss table respectively
    """
    I = insured_losses + 1
    ela_list = [('rup_id', U32), ('ass_id', U32), ('loss', (F32, I))]
    elt_list = [('rup_id', U32), ('loss', (F32, I))]
    return numpy.dtype(ela_list), numpy.dtype(elt_list)


@parallel.litetask
def build_agg_curve(lr_data, insured_losses, ses_ratio, curve_resolution, L,
                    monitor):
    """
    Build the aggregate loss curve in parallel for each loss type
    and realization pair.

    :param lr_data:
        a list of triples `(l, r, data)` where `l` is the loss type index,
        `r` is the realization index and `data` is an array of kind
        `(rupture_id, loss)` or `(rupture_id, loss, loss_ins)`
    :param bool insured_losses:
        job.ini configuration parameter
    :param ses_ratio:
        a ratio obtained from ses_per_logic_tree_path
    :param curve_resolution:
        the number of discretization steps for the loss curve
    :param L:
        the number of loss types
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary (r, l, i) -> (losses, poes, avg)
    """
    result = {}
    for l, r, data in lr_data:
        if len(data) == 0:  # realization with no losses
            continue
        if insured_losses:
            gloss = data['loss'][:, 0]
            iloss = data['loss'][:, 1]
        else:
            gloss = data['loss']
        losses, poes = scientific.event_based(
            gloss, ses_ratio, curve_resolution)
        avg = scientific.average_loss((losses, poes))
        result[l, r, 'losses'] = losses
        result[l, r, 'poes'] = poes
        result[l, r, 'avg'] = avg
        if insured_losses:
            losses_ins, poes_ins = scientific.event_based(
                iloss, ses_ratio, curve_resolution)
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


def _aggregate_output(output, compositemodel, agg, idx, result, monitor):
    # update the result dictionary and the agg array with each output
    assets = output.assets
    aid = assets[0].ordinal
    for (l, r), out in sorted(output.items()):
        indices = numpy.array([idx[eid] for eid in out.eids])

        # asslosses
        if monitor.asset_loss_table:
            data = [(eid, aid, loss)
                    for eid, loss in zip(out.eids, out.losses)
                    if loss.sum() > 0]
            result['ASSLOSS'][l, r].append(
                numpy.array(data, monitor.ela_dt))

        # agglosses
        agg[indices, l, r] += out.losses

        # dictionaries asset_idx -> array of counts
        if compositemodel.curve_builders[l].user_provided:
            result['RC'][l, r].append({aid: out.counts_matrix})
            if out.insured_counts_matrix.sum():
                result['IC'][l, r].append({aid: out.insured_counts_matrix})

        # average losses
        if monitor.avg_losses:
            result['AVGLOSS'][l, r][aid] += out.average_loss


@parallel.litetask
def event_based_risk(riskinput, riskmodel, rlzs_assoc, assetcol, monitor):
    """
    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
    :param assetcol:
        AssetCollection instance
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary of numpy arrays of shape (L, R)
    """
    lti = riskmodel.lti  # loss type -> index
    L, R = len(lti), len(rlzs_assoc.realizations)
    I = monitor.insured_losses + 1
    eids = riskinput.eids
    E = len(eids)
    idx = dict(zip(eids, range(E)))
    agg = numpy.zeros((E, L, R, I), F32)

    def zeroN():
        return numpy.zeros((monitor.num_assets, I))
    result = dict(RC=square(L, R, list), IC=square(L, R, list),
                  AGGLOSS=square(L, R, list))
    if monitor.asset_loss_table:
        result['ASSLOSS'] = square(L, R, list)
    if monitor.avg_losses:
        result['AVGLOSS'] = square(L, R, zeroN)

    agglosses_mon = monitor('aggregate losses', measuremem=False)
    for output in riskmodel.gen_outputs(
            riskinput, rlzs_assoc, monitor, assetcol):
        with agglosses_mon:
            _aggregate_output(output, riskmodel, agg, idx, result, monitor)
    for (l, r), lst in numpy.ndenumerate(result['AGGLOSS']):
        records = numpy.array(
            [(eids[i], loss) for i, loss in enumerate(agg[:, l, r])
             if loss.sum() > 0], monitor.elt_dt)
        result['AGGLOSS'][l, r] = records
    for (l, r), lst in numpy.ndenumerate(result['RC']):
        result['RC'][l, r] = sum(lst, AccumDict())
    for (l, r), lst in numpy.ndenumerate(result['IC']):
        result['IC'][l, r] = sum(lst, AccumDict())

    # store the size of the GMFs
    result['gmfbytes'] = monitor.gmfbytes
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
            _, indices = sliceobj
            return self.__class__(n, len(indices))
        else:
            raise ValueError('Not a valid slice: %r' % sliceobj)


@base.calculators.add('event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the event loss table and
    fixed ratios loss curves.
    """
    pre_calculator = 'event_based'
    core_task = event_based_risk
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
        self.N = len(self.assetcol)
        self.E = len(self.etags)
        logging.info('Populating the risk inputs')
        all_ruptures = []
        for serial in self.datastore['sescollection']:
            all_ruptures.append(self.datastore['sescollection/' + serial])
        all_ruptures.sort(key=operator.attrgetter('weight'), reverse=True)
        if not self.riskmodel.covs:
            # do not generate epsilons
            eps = FakeMatrix(self.N, self.E)
        else:
            eps = riskinput.make_eps(
                self.assets_by_site, self.E, oq.master_seed,
                oq.asset_correlation)
            logging.info('Generated %s epsilons', eps.shape)

        event_based.fix_minimum_intensity(oq.minimum_intensity, oq.imtls)

        # NB: self.riskinputs is a generator and it is used only once
        self.riskinputs = self.riskmodel.build_inputs_from_ruptures(
            self.sitecol.complete, all_ruptures, oq.truncation_level,
            correl_model, oq.minimum_intensity, eps, oq.concurrent_tasks or 1)

        # preparing empty datasets
        loss_types = self.riskmodel.loss_types
        self.C = self.oqparam.loss_curve_resolution
        self.L = L = len(loss_types)
        self.R = R = len(self.rlzs_assoc.realizations)
        self.I = self.oqparam.insured_losses

        # ugly: attaching an attribute needed in the task function
        mon = self.monitor
        mon.num_assets = self.count_assets()
        mon.avg_losses = self.oqparam.avg_losses
        mon.asset_loss_table = self.oqparam.asset_loss_table
        mon.insured_losses = self.I

        self.N = N = len(self.assetcol)
        self.E = len(self.datastore['etags'])

        # average losses, stored in a composite array of shape N, R
        multi_avg_dt = self.riskmodel.loss_type_dt(insured=self.I)
        self.avg_losses = numpy.zeros((N, R), multi_avg_dt)

        self.ass_loss_table = square(L, R, lambda: None)
        self.agg_loss_table = square(L, R, lambda: None)

        self.ela_dt, self.elt_dt = mon.ela_dt, mon.elt_dt = build_el_dtypes(
            self.I)
        for (l, r) in itertools.product(range(L), range(R)):
            lt = loss_types[l]
            if self.oqparam.asset_loss_table:
                self.ass_loss_table[l, r] = self.datastore.create_dset(
                    'ass_loss_table/rlz-%03d/%s' % (r, lt), self.ela_dt)
            self.agg_loss_table[l, r] = self.datastore.create_dset(
                'agg_loss_table/rlz-%03d/%s' % (r, lt), self.elt_dt)

    def execute(self):
        """
        Run the event_based_risk calculator and aggregate the results
        """
        self.saved = collections.Counter()  # nbytes per HDF5 key
        self.ass_bytes = 0
        self.agg_bytes = 0
        self.gmfbytes = 0
        rlz_ids = getattr(self.oqparam, 'rlz_ids', ())
        if rlz_ids:
            self.rlzs_assoc = self.rlzs_assoc.extract(rlz_ids)
        return starmap(
            self.core_task.__func__,
            ((riskinput, self.riskmodel, self.rlzs_assoc,
              self.assetcol, self.monitor.new('task'))
             for riskinput in self.riskinputs)).reduce(
                     agg=self.agg, posthook=self.save_data_transfer)

    def agg(self, acc, result):
        """
        Aggregate losses and store them in the datastore.

        :param acc: accumulator dictionary
        :param result: dictionary coming from event_based_risk
        """
        self.gmfbytes += result.pop('gmfbytes')
        with self.monitor('saving event loss tables', autoflush=True):
            if self.oqparam.asset_loss_table:
                for (l, r), arrays in numpy.ndenumerate(result.pop('ASSLOSS')):
                    for array in arrays:
                        self.ass_loss_table[l, r].extend(array)
                        self.ass_bytes += array.nbytes
            for (l, r), array in numpy.ndenumerate(result.pop('AGGLOSS')):
                self.agg_loss_table[l, r].extend(array)
                self.agg_bytes += array.nbytes
            self.datastore.hdf5.flush()

        return acc + result

    def post_execute(self, result):
        """
        Save the event loss table in the datastore.

        :param result:
            the dictionary returned by the .execute method
        """
        logging.info('Generated %s of GMFs', humansize(self.gmfbytes))
        self.datastore.save('job_info', {'gmfbytes': self.gmfbytes})

        if self.oqparam.asset_loss_table:
            asslt = self.datastore['ass_loss_table']
            asslt.attrs['nbytes'] = self.ass_bytes
            for rlz, dset in asslt.items():
                for ds in dset.values():
                    ds.attrs['nonzero_fraction'] = len(ds) / (self.N * self.E)

        agglt = self.datastore['agg_loss_table']
        agglt.attrs['nbytes'] = self.agg_bytes
        for rlz, dset in agglt.items():
            for ds in dset.values():
                ds.attrs['nonzero_fraction'] = len(ds) / self.E

        insured_losses = self.oqparam.insured_losses
        ses_ratio = self.oqparam.ses_ratio
        saved = self.saved
        self.N = N = len(self.assetcol)
        self.R = R = len(self.rlzs_assoc.realizations)
        ltypes = self.riskmodel.loss_types

        self.loss_curve_dt, self.loss_maps_dt = (
            self.riskmodel.build_loss_dtypes(
                self.oqparam.conditional_loss_poes, self.I))

        self.vals = {}  # asset values by loss_type
        for ltype in ltypes:
            asset_values = []
            for assets in self.assets_by_site:
                for asset in assets:
                    asset_values.append(asset.value(
                        ltype, self.oqparam.time_event))
            self.vals[ltype] = numpy.array(asset_values)

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
                    for i, avalue in enumerate(self.vals[lt]):
                        avg_losses_lt[i, r] = avgloss[i, 0] * avalue
                        if self.oqparam.insured_losses:
                            self.avg_losses[lt + '_ins'][i, r] = (
                                avgloss[i, 1] * avalue)
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
            oq.loss_curve_resolution, scientific.normalize_curves_eb,
            oq.insured_losses)

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
        if self.loss_maps_dt:
            with self.monitor('building loss_maps-rlzs'):
                if (self.oqparam.conditional_loss_poes and
                        'rcurves-rlzs' in self.datastore):
                    loss_maps = numpy.zeros((N, R), self.loss_maps_dt)
                    rcurves = self.datastore['rcurves-rlzs']
                    for cb in self.riskmodel.curve_builders:
                        if cb.user_provided:
                            lm = loss_maps[cb.loss_type]
                            for r, lmaps in cb.build_loss_maps(
                                    self.assetcol.array, rcurves):
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
        lr_data = [(l, r, dset.dset.value) for (l, r), dset in
                   numpy.ndenumerate(self.agg_loss_table)]
        ses_ratio = self.oqparam.ses_ratio
        result = parallel.apply_reduce(
            build_agg_curve, (lr_data, self.I, ses_ratio, C, self.L,
                              self.monitor('')),
            concurrent_tasks=self.oqparam.concurrent_tasks)
        agg_curve = numpy.zeros(self.R, loss_curve_dt)
        for l, r, name in result:
            agg_curve[lts[l]][name][r] = result[l, r, name]
        if oq.individual_curves:
            self.datastore['agg_curve-rlzs'] = agg_curve
            self.saved['agg_curve-rlzs'] = agg_curve.nbytes

        if self.R > 1:
            self.build_agg_curve_stats(builder, agg_curve, loss_curve_dt)

    # ################### methods to compute statistics  #################### #

    def _collect_all_data(self):
        # return a list of list of outputs
        if 'rcurves-rlzs' not in self.datastore:
            return []
        all_data = []
        assets = self.datastore['asset_refs'].value[self.assetcol.array['idx']]
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
            asset_values = self.vals[loss_type]
            data = []
            for rlz in rlzs:
                average_losses = avg_losses[loss_type][:, rlz.ordinal]
                average_insured_losses = (
                    avg_losses[loss_type + '_ins'][:, rlz.ordinal]
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
        loss_curves = numpy.zeros((self.N, self.Q1), self.loss_curve_dt)
        if oq.conditional_loss_poes:
            loss_maps = numpy.zeros((self.N, self.Q1), self.loss_maps_dt)
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
            loss_curves[cb.loss_type] = curves.T
            if oq.conditional_loss_poes:
                loss_maps[cb.loss_type] = maps.T

        self.datastore['loss_curves-stats'] = loss_curves
        if oq.conditional_loss_poes:
            self.datastore['loss_maps-stats'] = loss_maps

        if oq.avg_losses:  # stats for avg_losses
            stats = scientific.SimpleStats(rlzs, oq.quantile_loss_curves)
            stats.compute('avg_losses-rlzs', self.datastore)

        self.datastore.hdf5.flush()

    def build_agg_curve_stats(self, builder, agg_curve, loss_curve_dt):
        """
        Build and save `agg_curve-stats` in the HDF5 file.

        :param builder:
            :class:`openquake.risklib.scientific.StatsBuilder` instance
        :param agg_curve:
            array of aggregate curves, one per realization
        :param loss_curve_dt:
            numpy dtype for loss curves
        """
        rlzs = self.datastore['rlzs_assoc'].realizations
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
