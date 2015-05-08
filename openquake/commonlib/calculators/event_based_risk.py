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
from openquake.commonlib import readinput, parallel
from openquake.risklib import riskinput, scientific


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
        a dictionary rlz.ordinal -> (loss_type, tag) -> [(asset.id, loss), ...]
    """
    specific = set(monitor.oqparam.specific_assets)
    acc = AccumDict({rlz.ordinal: AccumDict()
                     for rlz in rlzs_assoc.realizations})
    # rlz.ordinal -> (loss_type, tag) -> [(asset.id, loss), ...]
    for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc, monitor):
        for out in out_by_rlz:
            for tag, losses, ins_losses in zip(
                    out.tags, out.event_loss_per_asset,
                    out.insured_loss_per_asset):
                data = [(asset.id, loss, ins_loss)
                        for asset, loss, ins_loss in zip(
                            out.assets, losses, ins_losses)
                        if loss and asset.id in specific]
                acc[out.hid][out.loss_type, tag] = AccumDict(
                    data=data, loss=sum(losses), ins_loss=sum(ins_losses),
                    nonzero=sum(1 for loss in losses if loss),
                    total=len(losses))
    return acc


def mean_quantiles(quantiles):
    yield 'mean'
    for q in quantiles:
        yield 'quantile-%s' % q


def loss_map_names(conditional_loss_poes):
    names = []
    for clp in conditional_loss_poes:
        names.append('poe-%s' % clp)
    return names


@base.calculators.add('event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    pre_calculator = 'event_based_rupture'
    core_func = event_based_risk
    event_loss_asset = base.persistent_attribute('event_loss_asset')
    event_loss = base.persistent_attribute('event_loss')

    def riskinput_key(self, ri):
        """
        :param ri: riskinput object
        :returns: the SESCollection idx associated to it
        """
        return ri.col_idx

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some empty files in the export directory to store the gmfs
        (if any). If there were pre-existing files, they will be erased.
        """
        super(EventBasedRiskCalculator, self).pre_execute()

        oq = self.oqparam
        epsilon_sampling = getattr(oq, 'epsilon_sampling', 1000)

        correl_model = readinput.get_correl_model(oq)
        gsims_by_trt_id = self.rlzs_assoc.get_gsims_by_trt_id()
        assets_by_site = self.precalc.assets_by_site
        logging.info('Building the epsilons')

        logging.info('Populating the risk inputs')
        rup_by_tag = self.precalc.rupture_by_tag
        all_ruptures = [rup_by_tag[tag] for tag in sorted(rup_by_tag)]
        num_samples = min(len(all_ruptures), epsilon_sampling)
        eps_dict = riskinput.make_eps_dict(
            assets_by_site, num_samples,
            getattr(oq, 'master_seed', 42),
            getattr(oq, 'asset_correlation', 0))
        logging.info('Generated %d epsilons', num_samples * len(eps_dict))
        self.riskinputs = list(self.riskmodel.build_inputs_from_ruptures(
            self.sitecol, assets_by_site, all_ruptures,
            gsims_by_trt_id, oq.truncation_level, correl_model, eps_dict,
            oq.concurrent_tasks or 1))
        logging.info('Built %d risk inputs', len(self.riskinputs))

    def post_execute(self, result):
        """
        Extract from the result dictionary
        rlz.ordinal -> (loss_type, tag) -> [(asset.id, loss), ...]
        several interesting outputs.
        """
        oq = self.oqparam
        rlzs = self.rlzs_assoc.realizations
        loss_types = self.riskmodel.get_loss_types()

        def loss_type_dt(dtype):
            return numpy.dtype([(lt, dtype) for lt in loss_types])

        R = oq.loss_curve_resolution
        self.loss_curve_dt = numpy.dtype(
            [('losses', (float, R)), ('poes', (float, R)), ('avg', float)])

        P = len(oq.conditional_loss_poes)
        lm_names = loss_map_names(oq.conditional_loss_poes)
        self.loss_map_dt = numpy.dtype([(f, float) for f in lm_names])

        self.asset_dict = {
            a.id: a for assets in self.precalc.assets_by_site for a in assets
            if a.id in self.oqparam.specific_assets}
        self.specific_assets = specific_assets = [
            self.asset_dict[a] for a in sorted(self.oqparam.specific_assets)]

        N = len(specific_assets)

        event_loss_asset = numpy.zeros(len(rlzs), loss_type_dt(object))
        event_loss = numpy.zeros(len(rlzs), loss_type_dt(object))

        loss_curves = numpy.zeros(N, loss_type_dt(self.loss_curve_dt))
        ins_curves = numpy.zeros(N, loss_type_dt(self.loss_curve_dt))
        loss_maps = numpy.zeros(N, loss_type_dt(self.loss_map_dt))
        agg_loss_curve = numpy.zeros(1, loss_type_dt(self.loss_curve_dt))

        for i in sorted(result):
            rlz = rlzs[i]

            data_by_lt_tag = result[i]
            # (loss_type, asset_id) -> [(tag, loss, ins_loss), ...]
            elass = {(loss_type, asset.id): [] for asset in specific_assets
                     for loss_type in loss_types}
            elagg = []  # aggregate event loss
            nonzero = total = 0
            for loss_type, tag in data_by_lt_tag:
                d = data_by_lt_tag[loss_type, tag]
                for asset_ref, loss, ins_loss in sorted(d['data']):
                    elass[loss_type, asset_ref].append((tag, loss, ins_loss))

                # aggregates
                elagg.append((loss_type, tag, d['loss'], d['ins_loss']))
                nonzero += d['nonzero']
                total += d['total']
            logging.info('rlz=%d: %d/%d nonzero losses', i, nonzero, total)

            if elass:
                data_by_lt = collections.defaultdict(list)
                for (loss_type, asset_id), rows in elass.iteritems():
                    for tag, loss, ins_loss in rows:
                        data_by_lt[loss_type].append(
                            (tag, asset_id, loss, ins_loss))
                for loss_type, data in data_by_lt.iteritems():
                    event_loss_asset[i][loss_type] = sorted(data)

                    # build the loss curves per asset
                    lc = self.build_loss_curves(elass, loss_type, 1)
                    loss_curves[loss_type] = lc

                    if oq.insured_losses:
                        # build the insured loss curves per asset
                        ic = self.build_loss_curves(elass, loss_type, 2)
                        ins_curves[loss_type] = ic

                    if oq.conditional_loss_poes:
                        # build the loss maps per asset, array of shape (N, P)
                        losses_poes = numpy.array(  # shape (N, 2, R)
                            [lc['losses'], lc['poes']]).transpose(1, 0, 2)
                        lmaps = scientific.loss_map_matrix(
                            oq.conditional_loss_poes, losses_poes)  # (P, N)
                        for lm, lmap in zip(lm_names, lmaps):
                            loss_maps[loss_type][lm] = lmap

            self.store('loss_curves', rlz.uid, loss_curves)
            if oq.insured_losses:
                self.store('ins_curves', rlz.uid, ins_curves)
            if oq.conditional_loss_poes:
                self.store('loss_maps', rlz.uid, loss_maps)

            if elagg:
                for loss_type, rows in groupby(
                        elagg, operator.itemgetter(0)).iteritems():
                    event_loss[i][loss_type] = [row[1:] for row in rows]
                    # aggregate loss curve for all tags
                    losses, poes, avg, _ = self.build_agg_loss_curve_and_map(
                        [loss for _lt, _tag, loss, _ins_loss in rows])
                    agg_loss_curve[loss_type] = [(losses, poes, avg)]
                    # NB: the aggregated loss_map is not stored

        self.event_loss_asset = event_loss_asset
        self.event_loss = event_loss

        # export statistics (i.e. mean and quantiles) for curves and maps
        if len(self.rlzs_assoc.realizations) > 1:

            Q = 1 + len(oq.quantile_loss_curves)
            loss_curve_stats = numpy.zeros(
                (Q, N), loss_type_dt(self.loss_curve_dt))
            ins_curve_stats = numpy.zeros(
                (Q, N), loss_type_dt(self.loss_curve_dt))
            loss_map_stats = numpy.zeros(
                (Q, N), loss_type_dt(self.loss_map_dt))

            for stat in self.calc_stats():  # one stat for each loss_type
                curves, ins_curves, maps = scientific.get_stat_curves(stat)
                loss_curve_stats[:][stat.loss_type] = curves
                if oq.insured_losses:
                    ins_curve_stats[:][stat.loss_type] = ins_curves
                if oq.conditional_loss_poes:
                    loss_map_stats[:][stat.loss_type] = maps

            for i, q in enumerate(mean_quantiles(oq.quantile_loss_curves)):
                self.store('loss_curves', q, loss_curve_stats[i])
                if oq.insured_losses:
                    self.store('ins_curves', q, ins_curve_stats[i])
                if oq.conditional_loss_poes:
                    self.store('loss_maps', q, loss_map_stats[i])

    def build_agg_loss_curve_and_map(self, losses):
        """
        Build a loss curve from a set of losses with length give by
        the parameter loss_curve_resolution.

        :param losses: a sequence of losses
        :returns: a quartet (losses, poes, av, loss_map)
        """
        oq = self.oqparam
        clp = oq.conditional_loss_poes
        losses_poes = scientific.event_based(
            losses, tses=oq.tses, time_span=oq.investigation_time,
            curve_resolution=oq.loss_curve_resolution)
        loss_map = scientific.loss_map_matrix(
            clp, [losses_poes]).reshape(len(clp)) if clp else None
        return (losses_poes[0], losses_poes[1],
                scientific.average_loss(losses_poes), loss_map)

    def build_loss_curves(self, elass, loss_type, i):
        """
        Build loss curves per asset from a set of losses with length given by
        the parameter loss_curve_resolution.

        :param elass: a dict (loss_type, asset_id) -> (tag, loss, ins_loss)
        :param loss_type: the loss_type
        :param i: an index 1 (loss curves) or 2 (insured losses)
        :returns: an array of loss curves, one for each asset
        """
        oq = self.oqparam
        R = oq.loss_curve_resolution
        lcs = []
        for asset in self.specific_assets:
            all_losses = [loss[i] for loss in elass[loss_type, asset.id]]
            if all_losses:
                losses, poes = scientific.event_based(
                    all_losses, tses=oq.tses, time_span=oq.investigation_time,
                    curve_resolution=R)
                avg = scientific.average_loss((losses, poes))
            else:
                losses, poes = numpy.zeros(R), numpy.zeros(R)
                avg = 0
            lcs.append((losses, poes, avg))
        return numpy.array(lcs, self.loss_curve_dt)

    def calc_stats(self):
        """
        Compute all statistics starting from the loss curves for each asset.
        Yield a statistical output object for each loss type.
        """
        oq = self.oqparam
        rlzs = self.rlzs_assoc.realizations
        assets = self.specific_assets
        stats = scientific.StatsBuilder(
            oq.quantile_loss_curves, oq.conditional_loss_poes, [],
            scientific.normalize_curves_eb)
        with self.datastore.h5file(('loss_curves', 'hdf5')) as loss_curves:
            for loss_type in self.riskmodel.get_loss_types():
                outputs = []
                for rlz in rlzs:
                    lcs = loss_curves[rlz.uid][loss_type]
                    losses_poes = numpy.array(  # shape (N, 2, R)
                        [lcs['losses'], lcs['poes']]).transpose(1, 0, 2)
                    out = scientific.Output(
                        assets, loss_type, rlz.ordinal, rlz.weight,
                        loss_curves=losses_poes, insured_curves=None)
                    outputs.append(out)
                if outputs:
                    yield stats.build(outputs)
                else:
                    # this should never happen
                    logging.error('No outputs found for loss_type=%s',
                                  loss_type)

    def store(self, name, dset, curves):
        """
        Store all kind of curves, loss curves, maps and aggregates

        :param dset: the HDF5 dataset where to store the curves
        :param curves: an array of N curves to store
        """
        with self.datastore.h5file((name, 'hdf5')) as h5f:
            h5f[dset] = curves
