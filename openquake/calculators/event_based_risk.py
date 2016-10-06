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
import functools
import collections

import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import zip
from openquake.baselib.general import AccumDict, humansize, block_splitter
from openquake.calculators import base, event_based
from openquake.commonlib import parallel, calc
from openquake.risklib import riskinput, scientific
from openquake.commonlib.parallel import starmap

U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
getweight = operator.attrgetter('weight')


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


def _aggregate(outputs, compositemodel, agg, ass, idx, result, monitor):
    # update the result dictionary and the agg array with each output
    for out in outputs:
        l, r = out.lr
        asset_ids = [a.ordinal for a in out.assets]
        loss_type = compositemodel.loss_types[l]
        indices = numpy.array([idx[eid] for eid in out.eids])

        cb = compositemodel.curve_builders[l]
        if cb.user_provided:
            counts_matrix = cb.build_counts(out.loss_ratios[:, :, 0])
            result['RC'][l, r] += dict(zip(asset_ids, counts_matrix))
            if monitor.insured_losses:
                result['IC'][l, r] += dict(
                    zip(asset_ids, cb.build_counts(out.loss_ratios[:, :, 1])))

        for i, asset in enumerate(out.assets):
            aid = asset.ordinal
            loss_ratios = out.loss_ratios[i]
            losses = loss_ratios * asset.value(loss_type)

            # average losses
            if monitor.avg_losses:
                result['AVGLOSS'][l, r][aid] += (
                    loss_ratios.sum(axis=0) * monitor.ses_ratio)

            # asset losses
            if monitor.asset_loss_table:
                data = [(eid, aid, loss)
                        for eid, loss in zip(out.eids, losses)
                        if loss.sum() > 0]
                if data:
                    ass[l, r].append(numpy.array(data, monitor.ela_dt))

            # agglosses
            agg[indices, l, r] += losses


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
    ass = collections.defaultdict(list)

    def zeroN():
        return numpy.zeros((monitor.num_assets, I))
    result = dict(RC=square(L, R, AccumDict), IC=square(L, R, AccumDict),
                  AGGLOSS=AccumDict(), ASSLOSS=AccumDict())
    if monitor.avg_losses:
        result['AVGLOSS'] = square(L, R, zeroN)

    outputs = riskmodel.gen_outputs(riskinput, rlzs_assoc, monitor, assetcol)
    _aggregate(outputs, riskmodel, agg, ass, idx, result, monitor)
    for (l, r) in itertools.product(range(L), range(R)):
        records = [(eids[i], loss) for i, loss in enumerate(agg[:, l, r])
                   if loss.sum() > 0]
        if records:
            result['AGGLOSS'][l, r] = numpy.array(records, monitor.elt_dt)
    for lr in ass:
        if ass[lr]:
            result['ASSLOSS'][lr] = numpy.concatenate(ass[lr])

    # store the size of the GMFs
    result['gmfbytes'] = monitor.gmfbytes
    return result


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
        Read the precomputed ruptures (or compute them on the fly)
        """
        super(EventBasedRiskCalculator, self).pre_execute()
        calc.check_overflow(self)
        if not self.riskmodel:  # there is no riskmodel, exit early
            self.execute = lambda: None
            self.post_execute = lambda result: None
            return

    def execute(self):
        """
        Run the event_based_risk calculator and aggregate the results
        """
        oq = self.oqparam
        correl_model = oq.get_correl_model()
        self.N = len(self.assetcol)
        self.E = len(self.datastore['events'])
        logging.info('Populating the risk inputs')
        all_ruptures = []
        preprecalc = getattr(self.precalc, 'precalc', None)
        if preprecalc:  # the ruptures are already in memory
            for grp_id, sesruptures in preprecalc.result.items():
                for sr in sesruptures:
                    all_ruptures.append(sr)
        else:  # read the ruptures from the datastore
            for serial in self.datastore['sescollection']:
                rup = self.datastore['sescollection/' + serial]
                all_ruptures.append(rup)
        all_ruptures.sort(key=operator.attrgetter('serial'))
        if not self.riskmodel.covs:
            # do not generate epsilons
            eps = None
        else:
            eps = riskinput.make_eps(
                self.assets_by_site, self.E, oq.master_seed,
                oq.asset_correlation)
            logging.info('Generated %s epsilons', eps.shape)

        # preparing empty datasets
        loss_types = self.riskmodel.loss_types
        self.C = self.oqparam.loss_curve_resolution
        self.L = L = len(loss_types)
        self.R = R = len(self.rlzs_assoc.realizations)
        self.I = self.oqparam.insured_losses

        # ugly: attaching attributes needed in the task function
        mon = self.monitor
        mon.num_assets = self.count_assets()
        mon.avg_losses = self.oqparam.avg_losses
        mon.asset_loss_table = self.oqparam.asset_loss_table
        mon.insured_losses = self.I
        mon.ses_ratio = (
            oq.risk_investigation_time or oq.investigation_time) / (
                oq.investigation_time * oq.ses_per_logic_tree_path)

        self.N = N = len(self.assetcol)
        self.E = len(self.datastore['events'])

        # average losses, stored in a composite array of shape N, R
        self.avg_losses = numpy.zeros((N, R), oq.loss_dt())

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

        self.saved = collections.Counter()  # nbytes per HDF5 key
        self.ass_bytes = 0
        self.agg_bytes = 0
        self.gmfbytes = 0
        rlz_ids = getattr(self.oqparam, 'rlz_ids', ())
        if rlz_ids:
            self.rlzs_assoc = self.rlzs_assoc.extract(rlz_ids)

        if not oq.minimum_intensity:
            # infer it from the risk models if not directly set in job.ini
            oq.minimum_intensity = self.riskmodel.get_min_iml()
        min_iml = calc.fix_minimum_intensity(
            oq.minimum_intensity, oq.imtls)
        if min_iml.sum() == 0:
            logging.warn('The GMFs are not filtered: '
                         'you may want to set a minimum_intensity')
        else:
            logging.info('minimum_intensity=%s', oq.minimum_intensity)
        csm_info = self.datastore['csm_info']
        grp_trt = {sg.id: sg.trt for sm in csm_info.source_models
                   for sg in sm.src_groups}
        with self.monitor('building riskinputs', autoflush=True):
            riskinputs = self.riskmodel.build_inputs_from_ruptures(
                grp_trt, list(oq.imtls), self.sitecol.complete, all_ruptures,
                oq.truncation_level, correl_model, min_iml, eps,
                oq.concurrent_tasks or 1)
            # NB: I am using generators so that the tasks are submitted one at
            # the time, without keeping all of the arguments in memory
            res = starmap(
                self.core_task.__func__,
                ((riskinput, self.riskmodel, self.rlzs_assoc,
                  self.assetcol, self.monitor.new('task'))
                 for riskinput in riskinputs)).submit_all()
        acc = functools.reduce(self.agg, res, AccumDict())
        self.save_data_transfer(res)
        return acc

    def agg(self, acc, result):
        """
        Aggregate losses and store them in the datastore.

        :param acc: accumulator dictionary
        :param result: dictionary coming from event_based_risk
        """
        self.gmfbytes += result.pop('gmfbytes')
        with self.monitor('saving event loss tables', autoflush=True):
            if self.oqparam.asset_loss_table:
                for lr, array in sorted(result.pop('ASSLOSS').items()):
                    hdf5.extend(self.ass_loss_table[lr], array)
                    self.ass_bytes += array.nbytes
            for lr, array in sorted(result.pop('AGGLOSS').items()):
                hdf5.extend(self.agg_loss_table[lr], array)
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
        if self.gmfbytes == 0:
            raise RuntimeError('No GMFs were generated, perhaps they were '
                               'all below the minimum_intensity threshold')

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
                if 'rcurves-rlzs' in self.datastore:
                    self.compute_store_stats(rlzs, builder)
                if oq.avg_losses:  # stats for avg_losses
                    stats = scientific.SimpleStats(
                        rlzs, oq.quantile_loss_curves)
                    stats.compute_and_store('avg_losses', self.datastore)

        self.datastore.hdf5.flush()

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
        lr_data = [(l, r, dset.value) for (l, r), dset in
                   numpy.ndenumerate(self.agg_loss_table)]
        ses_ratio = self.oqparam.ses_ratio
        result = parallel.apply(
            build_agg_curve, (lr_data, self.I, ses_ratio, C, self.L,
                              self.monitor('')),
            concurrent_tasks=self.oqparam.concurrent_tasks).reduce()
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
        # called only if 'rcurves-rlzs' in dstore; return a list of outputs
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
        rlzs = self.datastore['csm_info'].get_rlzs_assoc().realizations
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

elt_dt = numpy.dtype([('rup_id', U32), ('loss', F32)])


def losses_by_taxonomy(riskinput, riskmodel, rlzs_assoc, assetcol, monitor):
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
        a numpy array of shape (T, L, R)
    """
    lti = riskmodel.lti  # loss type -> index
    L, R = len(lti), len(rlzs_assoc.realizations)
    T = len(assetcol.taxonomies)
    A = len(assetcol)
    taxonomy_id = {t: i for i, t in enumerate(sorted(assetcol.taxonomies))}
    losses = numpy.zeros((T, L, R), F64)
    avglosses = numpy.zeros((A, L, R), F64) if monitor.avg_losses else None
    agglosses = AccumDict(
        {lr: AccumDict() for lr in itertools.product(range(L), range(R))})
    for out in riskmodel.gen_outputs(riskinput, rlzs_assoc, monitor, assetcol):
        # NB: out.assets is a non-empty list of assets with the same taxonomy
        t = taxonomy_id[out.assets[0].taxonomy]
        l, r = out.lr
        losses[t, l, r] += out.alosses.sum()
        if monitor.avg_losses:
            for i, loss in enumerate(out.alosses):
                if loss:
                    avglosses[i, l, r] += loss
        agglosses[l, r] += {eid: loss for eid, loss in
                            zip(out.eids, out.elosses) if loss}

    # convert agglosses into arrays to reduce the data transfer
    agglosses = {lr: numpy.array(sorted(agglosses[lr].items()), elt_dt)
                 for lr in agglosses}
    return AccumDict(losses=losses, avglosses=avglosses, agglosses=agglosses,
                     gmfbytes=monitor.gmfbytes)

save_ruptures = event_based.EventBasedRuptureCalculator.__dict__[
    'save_ruptures']


@base.calculators.add('ebrisk')
class EbriskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the total losses by taxonomy
    """
    pre_calculator = None
    is_stochastic = True
    compute_ruptures = staticmethod(event_based.compute_ruptures)

    # TODO: if the number of source models is larger than concurrent_tasks
    # a different strategy should be used; the one used here is good when
    # there are few source models, so that we cannot parallelize on those
    def build_starmap(self, ssm, sitecol, assetcol, riskmodel, imts,
                      trunc_level, correl_model, min_iml, monitor):
        """
        :param ssm: CompositeSourceModel containing a single source model
        :param sitecol: a SiteCollection instance
        :param assetcol: an AssetCollection instance
        :param riskmodel: a RiskModel instance
        :param imts: a list of Intensity Measure Types
        :param trunc_level: truncation level
        :param correl_model: correlation model
        :param min_iml: vector of minimum intensities, one per IMT
        :param monitor: a Monitor instance
        :returns: a pair (starmap, dictionary)
        """
        ruptures_by_grp = AccumDict()
        num_ruptures = 0
        num_events = 0
        allargs = []
        grp_trt = {}
        # collect the sources
        maxweight = ssm.get_maxweight(self.oqparam.concurrent_tasks)
        logging.info('Using a maxweight of %d', maxweight)
        for src_group in ssm.src_groups:
            grp_trt[src_group.id] = trt = src_group.trt
            gsims = ssm.gsim_lt.values[trt]
            for block in block_splitter(src_group, maxweight, getweight):
                allargs.append((block, self.sitecol, gsims, monitor))
        # collect the ruptures
        for dic in parallel.starmap(self.compute_ruptures, allargs):
            ruptures_by_grp += dic
            [rupts] = dic.values()
            num_ruptures += len(rupts)
            num_events += dic.num_events
        ruptures_by_grp.num_events = num_events
        save_ruptures(self, ruptures_by_grp)

        # determine the realizations
        rlzs_assoc = ssm.info.get_rlzs_assoc(
            count_ruptures=lambda grp: len(ruptures_by_grp.get(grp.id, 0)))
        allargs = []
        # prepare the risk inputs
        ruptures_per_block = self.oqparam.ruptures_per_block
        for src_group in ssm.src_groups:
            for rupts in block_splitter(
                    ruptures_by_grp[src_group.id], ruptures_per_block):
                trt = grp_trt[rupts[0].grp_id]
                ri = riskinput.RiskInputFromRuptures(
                    trt, imts, sitecol, rupts, trunc_level,
                    correl_model, min_iml)
                allargs.append((ri, riskmodel, rlzs_assoc, assetcol, monitor))
        taskname = '%s#%d' % (losses_by_taxonomy.__name__, ssm.sm_id + 1)
        smap = starmap(losses_by_taxonomy, allargs, name=taskname)
        attrs = dict(num_ruptures={
            sg_id: len(rupts) for sg_id, rupts in ruptures_by_grp.items()},
                     num_events=num_events,
                     num_rlzs=len(rlzs_assoc.realizations),
                     sm_id=ssm.sm_id)
        return smap, attrs

    def gen_args(self):
        """
        Yield the arguments required by build_starmap, i.e. the
        source models, the asset collection, the riskmodel and others.
        """
        oq = self.oqparam
        correl_model = oq.get_correl_model()
        if not oq.minimum_intensity:
            # infer it from the risk models if not directly set in job.ini
            oq.minimum_intensity = self.riskmodel.get_min_iml()
        min_iml = calc.fix_minimum_intensity(oq.minimum_intensity, oq.imtls)
        if min_iml.sum() == 0:
            logging.warn('The GMFs are not filtered: '
                         'you may want to set a minimum_intensity')
        else:
            logging.info('minimum_intensity=%s', oq.minimum_intensity)
        self.csm.init_serials()
        imts = list(oq.imtls)
        for sm_id in range(len(self.csm.source_models)):
            ssm = self.csm.get_model(sm_id)
            monitor = self.monitor.new(
                avg_losses=oq.avg_losses,
                ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
                maximum_distance=oq.maximum_distance,
                samples=ssm.source_models[0].samples,
                seed=ssm.source_model_lt.seed)
            yield (ssm, self.sitecol, self.assetcol, self.riskmodel,
                   imts, oq.truncation_level, correl_model, min_iml, monitor)

    def execute(self):
        """
        Run the calculator and aggregate the results
        """
        num_rlzs = 0
        allres = []
        source_models = self.csm.info.source_models
        with self.monitor('sending riskinputs', autoflush=True):
            self.eid = 0
            for i, args in enumerate(self.gen_args()):
                smap, attrs = self.build_starmap(*args)
                logging.info(
                    'Generated %d/%d ruptures/events for source model #%d',
                    sum(attrs['num_ruptures'].values()), attrs['num_events'],
                    attrs['sm_id'] + 1)
                res = smap.submit_all()
                vars(res).update(attrs)
                allres.append(res)
                res.rlz_slice = slice(num_rlzs, num_rlzs + res.num_rlzs)
                num_rlzs += res.num_rlzs
                for sg in source_models[i].src_groups:
                    sg.eff_ruptures = res.num_ruptures[sg.id]
        self.datastore['csm_info'] = self.csm.info
        num_events = self.save_results(allres, num_rlzs)
        self.save_data_transfer(parallel.IterResult.sum(allres))
        return num_events

    def save_results(self, allres, num_rlzs):
        """
        :param allres: an iterable of result iterators
        :param num_rlzs: the total number of realizations
        :returns: the total number of events
        """
        self.L = len(self.riskmodel.lti)
        self.R = num_rlzs
        self.T = len(self.assetcol.taxonomies)
        self.A = len(self.assetcol)
        avg_losses = self.oqparam.avg_losses
        dset1 = self.datastore.create_dset(
            'losses_by_taxon', F64, (self.T, self.L, self.R))
        if avg_losses:
            dset2 = self.datastore.create_dset(
                'avglosses', F64, (self.A, self.L, self.R))
        num_events = 0
        self.gmfbytes = 0
        for res in allres:
            start, stop = res.rlz_slice.start, res.rlz_slice.stop
            r = stop - start
            taxlosses = numpy.zeros((self.T, self.L, r), F64)
            if avg_losses:
                avglosses = numpy.zeros((self.A, self.L, r), F64)
            for dic in res:
                if avg_losses:
                    avglosses += dic.pop('avglosses')
                taxlosses += dic.pop('losses')
                self.gmfbytes += dic.pop('gmfbytes')
                self.save_agglosses(dic.pop('agglosses'), start)
            logging.debug(
                'Saving results for source model #%d, realizations %d:%d',
                res.sm_id + 1, start, stop)
            dset1[:, :, start:stop] = taxlosses
            if avg_losses:
                dset2[:, :, start:stop] = avglosses
            if hasattr(res, 'ruptures_by_grp'):
                save_ruptures(self, res.ruptures_by_grp)
            num_events += res.num_events
        if avg_losses:
            self.datastore['avglosses'] = avglosses
        return num_events

    def save_agglosses(self, agglosses, offset):
        """
        Save the event loss tables incrementally.

        :param agglosses: a dictionary lr -> {eid: loss}
        :param offset: realization offset
        """
        with self.monitor('saving event loss tables', autoflush=True):
            for l, r in agglosses:
                loss_type = self.riskmodel.loss_types[l]
                key = 'agg_loss_table/rlz-%03d/%s' % (r + offset, loss_type)
                self.datastore.extend(key, agglosses[l, r])

    def post_execute(self, num_events):
        """
        Save an array of losses by taxonomy of shape (T, L, R).
        """
        if self.gmfbytes == 0:
            raise RuntimeError('No GMFs were generated, perhaps they were '
                               'all below the minimum_intensity threshold')
        logging.info('Generated %s of GMFs', humansize(self.gmfbytes))
        self.datastore.save('job_info', {'gmfbytes': self.gmfbytes})
        logging.info('Saved %s losses by taxonomy', (self.T, self.L, self.R))
        logging.info('Saved %d event losses', num_events)
        self.datastore.set_nbytes('agg_loss_table')
        self.datastore.set_nbytes('events')
