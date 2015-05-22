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
import functools
import collections

import numpy

from openquake.baselib.general import AccumDict, groupby
from openquake.commonlib.calculators import base
from openquake.commonlib import readinput, parallel, datastore
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
        a dictionary rlz.ordinal -> (loss_type, tag) -> AccumDict()
    """
    specific = set(monitor.oqparam.specific_assets)
    if monitor.num_assets <= 10:  # hack
        specific = set(a.id for assets in monitor.assets_by_site
                       for a in assets)
    acc = AccumDict({rlz.ordinal: AccumDict()
                     for rlz in rlzs_assoc.realizations})
    # rlz.ordinal -> (loss_type, tag) -> AccumDict
    for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc, monitor):
        for out in out_by_rlz:
            acc_rlz = acc[out.hid]
            acc_rlz[out.loss_type, 'counts_matrix'] = AccumDict(
                zip(out.assets, out.counts_matrix))
            for tag, losses, ins_losses in zip(
                    out.tags, out.event_loss_per_asset,
                    out.insured_loss_per_asset):
                data = [(asset.id, loss, ins_loss)
                        for asset, loss, ins_loss in zip(
                            out.assets, losses, ins_losses)
                        if loss and asset.id in specific]
                ad = AccumDict(
                    data=data, loss=sum(losses), ins_loss=sum(ins_losses),
                    nonzero=sum(1 for loss in losses if loss),
                    total=len(losses))
                # TODO: the names of the variables here are really bad:
                # things like (acc_rlz, ad, a) for the inner dictionaries.
                # The solution will be to refactor the input/output
                # and use more arrays instead than a dictionary of dictionaries
                # of dictionaries (bleah!)
                try:
                    a = acc_rlz[out.loss_type, tag]
                except KeyError:
                    acc_rlz[out.loss_type, tag] = ad
                else:
                    a += ad
    return acc


def _mean_quantiles(quantiles):
    yield 'mean'
    for q in quantiles:
        yield 'quantile-%s' % q


def _loss_map_names(conditional_loss_poes):
    names = []
    for clp in conditional_loss_poes:
        names.append('poe~%s' % clp)
    return names


def extract_avglosses(dstore, pattern):
    """
    Function extracting the average losses from the loss curves
    for each realization.

    :param dstore: a datastore object
    :param pattern: '/loss_curves-rlzs/%s' or '/agg_loss_curve-rlzs/%s'
    :returns: list of dictionaries loss_type -> avg losses per asset
    """
    rlzs = dstore['rlzs_assoc'].realizations
    loss_types = dstore['riskmodel'].get_loss_types()
    data = []
    for rlz in rlzs:
        curves = dstore[pattern % rlz.uid]
        data.append({lt: curves[lt]['avg'] for lt in loss_types})
    return data


@base.calculators.add('event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    pre_calculator = 'event_based_rupture'
    core_func = event_based_risk

    event_loss_asset = datastore.persistent_attribute('event_loss_asset')
    event_loss = datastore.persistent_attribute('event_loss')

    def riskinput_key(self, ri):
        """
        :param ri: riskinput object
        :returns: the SESCollection idx associated to it
        """
        return ri.col_id

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
        gsims_by_col = self.rlzs_assoc.get_gsims_by_col()
        assets_by_site = self.assets_by_site
        logging.info('Building the epsilons')

        logging.info('Populating the risk inputs')
        rup_by_tag = sum(self.datastore['sescollection'], AccumDict())
        all_ruptures = [rup_by_tag[tag] for tag in sorted(rup_by_tag)]
        num_samples = min(len(all_ruptures), epsilon_sampling)
        eps_dict = riskinput.make_eps_dict(
            assets_by_site, num_samples, oq.master_seed, oq.asset_correlation)
        logging.info('Generated %d epsilons', num_samples * len(eps_dict))

        self.riskinputs = list(self.riskmodel.build_inputs_from_ruptures(
            self.sitecol, all_ruptures, gsims_by_col, oq.truncation_level,
            correl_model, eps_dict, oq.concurrent_tasks or 1))
        logging.info('Built %d risk inputs', len(self.riskinputs))

    def zeros(self, shape, dtype):
        """
        Build a composite dtype from the given loss_types and dtype and
        return a zero array of the given shape.
        """
        loss_types = self.riskmodel.get_loss_types()
        dt = numpy.dtype([(lt, dtype) for lt in loss_types])
        return numpy.zeros(shape, dt)

    def post_execute(self, result):
        """
        Extract from the result dictionary
        rlz.ordinal -> (loss_type, tag) -> [(asset.id, loss), ...]
        several interesting outputs.
        """
        oq = self.oqparam
        self.rlzs_assoc = self.rlzs_assoc  # write anew
        rlzs = self.rlzs_assoc.realizations
        loss_types = self.riskmodel.get_loss_types()

        C = oq.loss_curve_resolution
        self.loss_curve_dt = numpy.dtype(
            [('losses', (float, C)), ('poes', (float, C)), ('avg', float)])

        if oq.conditional_loss_poes:
            lm_names = _loss_map_names(oq.conditional_loss_poes)
            self.loss_map_dt = numpy.dtype([(f, float) for f in lm_names])

        self.assets = assets = riskinput.sorted_assets(self.assets_by_site)

        self.specific_assets = specific_assets = [
            a for a in assets if a.id in self.oqparam.specific_assets]
        specific_asset_refs = set(self.oqparam.specific_assets)

        N = len(assets)

        event_loss_asset = [{} for rlz in rlzs]
        event_loss = [{} for rlz in rlzs]

        loss_curves = self.zeros(N, self.loss_curve_dt)
        ins_curves = self.zeros(N, self.loss_curve_dt)
        if oq.conditional_loss_poes:
            loss_maps = self.zeros(N, self.loss_map_dt)
        agg_loss_curve = self.zeros(1, self.loss_curve_dt)

        for i in sorted(result):
            rlz = rlzs[i]

            data_by_lt_tag = result[i]
            # (loss_type, asset_id) -> [(tag, loss, ins_loss), ...]
            elass = {(loss_type, asset.id): [] for asset in assets
                     for loss_type in loss_types}
            elagg = []  # aggregate event loss
            nonzero = total = 0
            for loss_type, tag in data_by_lt_tag:
                d = data_by_lt_tag[loss_type, tag]
                if tag == 'counts_matrix':
                    # the counts_matrix management is left for the future
                    continue

                for aid, loss, ins_loss in d['data']:
                    elass[loss_type, aid].append((tag, loss, ins_loss))

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
                    event_loss_asset[i][loss_type] = sorted(
                        (t, a, l, i) for t, a, l, i in data
                        if a in specific_asset_refs)

                    # build the loss curves per asset
                    lc = self.build_loss_curves(elass, loss_type, 1)
                    loss_curves[loss_type] = lc

                    if oq.insured_losses:
                        # build the insured loss curves per asset
                        ic = self.build_loss_curves(elass, loss_type, 2)
                        ins_curves[loss_type] = ic

                    if oq.conditional_loss_poes:
                        # build the loss maps per asset, array of shape (N, P)
                        losses_poes = numpy.array(  # shape (N, 2, C)
                            [lc['losses'], lc['poes']]).transpose(1, 0, 2)
                        lmaps = scientific.loss_map_matrix(
                            oq.conditional_loss_poes, losses_poes)  # (P, N)
                        for lm, lmap in zip(lm_names, lmaps):
                            loss_maps[loss_type][lm] = lmap

            self.store('/loss_curves', rlz, loss_curves)
            if oq.insured_losses:
                self.store('/ins_curves', rlz, ins_curves)
            if oq.conditional_loss_poes:
                self.store('/loss_maps', rlz, loss_maps)

            if elagg:
                for loss_type, rows in groupby(
                        elagg, operator.itemgetter(0)).iteritems():
                    event_loss[i][loss_type] = [row[1:] for row in rows]
                    # aggregate loss curve for all tags
                    losses, poes, avg, _ = self.build_agg_loss_curve_and_map(
                        [loss for _lt, _tag, loss, _ins_loss in rows])
                    # NB: there is no aggregate insured loss curve
                    agg_loss_curve[loss_type][0] = (losses, poes, avg)
                    # NB: the aggregated loss_map is not stored
                self.store('/agg_loss_curve', rlz, agg_loss_curve)

        if specific_assets:
            self.event_loss_asset = event_loss_asset
        self.event_loss = event_loss

        self.datastore['avglosses_rlzs'] = functools.partial(
            extract_avglosses, pattern='/loss_curves-rlzs/%s')
        self.datastore['agg_avgloss_rlzs'] = functools.partial(
            extract_avglosses, pattern='/agg_loss_curve-rlzs/%s')

        # store statistics (i.e. mean and quantiles) for curves and maps
        if len(self.rlzs_assoc.realizations) > 1:
            self.compute_store_stats('/loss_curves')
            self.compute_store_stats('/agg_loss_curve')

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

    def build_agg_loss_curve_and_map(self, losses):
        """
        Build a loss curve from a set of losses with length given by
        the parameter loss_curve_resolution.

        :param losses: a sequence of losses
        :returns: a quartet (losses, poes, avg, loss_map)
        """
        oq = self.oqparam
        clp = oq.conditional_loss_poes
        losses_poes = scientific.event_based(
            losses, tses=oq.tses, time_span=oq.risk_investigation_time,
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
        :param i: 1 for loss curves or 2 for insured losses
        :returns: an array of loss curves, one for each asset
        """
        oq = self.oqparam
        C = oq.loss_curve_resolution
        lcs = []
        for asset in self.assets:
            all_losses = [loss[i] for loss in elass[loss_type, asset.id]]
            if all_losses:
                losses, poes = scientific.event_based(
                    all_losses, tses=oq.tses,
                    time_span=oq.risk_investigation_time,
                    curve_resolution=C)
                avg = scientific.average_loss((losses, poes))
            else:
                losses, poes = numpy.zeros(C), numpy.zeros(C)
                avg = 0
            lcs.append((losses, poes, avg))
        return numpy.array(lcs, self.loss_curve_dt)

    def store(self, name, dset, curves):
        """
        Store loss curves, maps and aggregates

        :param name: the name of the HDF5 file
        :param dset: the dataset where to store the curves
        :param curves: an array of curves to store
        """
        if hasattr(dset, 'uid'):
            dset = dset.uid
            kind = 'rlzs'
        else:
            kind = 'stats'
        self.datastore['%s-%s/%s' % (name, kind, dset)] = curves

    # ################### methods to compute statistics  #################### #

    def build_stats(self, loss_curve_key):
        """
        Compute all statistics for the specified assets starting from the
        stored loss curves. Yield a statistical output object for each
        loss type.
        """
        oq = self.oqparam
        rlzs = self.rlzs_assoc.realizations
        stats = scientific.StatsBuilder(
            oq.quantile_loss_curves, oq.conditional_loss_poes, [],
            scientific.normalize_curves_eb)
        # NB: should we encounter memory issues in the future, the easy
        # solution is to split the specific assets in blocks and perform
        # the computation one block at the time
        for loss_type in self.riskmodel.get_loss_types():
            outputs = []
            for rlz in rlzs:
                key = '%s-rlzs/%s' % (loss_curve_key, rlz.uid)
                lcs = self.datastore[key][loss_type]
                assets = [None] if key.startswith('/agg') else self.assets
                losses_poes = numpy.array(  # -> shape (N, 2, C)
                    [lcs['losses'], lcs['poes']]).transpose(1, 0, 2)
                out = scientific.Output(
                    assets, loss_type, rlz.ordinal, rlz.weight,
                    loss_curves=losses_poes, insured_curves=None)
                outputs.append(out)
            yield stats.build(outputs)

    def compute_store_stats(self, loss_curve_key):
        """
        Compute and store the statistical outputs
        """
        oq = self.oqparam
        N = 1 if loss_curve_key.startswith('/agg_') else len(self.assets)
        Q = 1 + len(oq.quantile_loss_curves)
        loss_curve_stats = self.zeros((Q, N), self.loss_curve_dt)
        ins_curve_stats = self.zeros((Q, N), self.loss_curve_dt)
        if oq.conditional_loss_poes:
            loss_map_stats = self.zeros((Q, N), self.loss_map_dt)

        for stat in self.build_stats(loss_curve_key):
            # there is one stat for each loss_type
            curves, ins_curves, maps = scientific.get_stat_curves(stat)
            loss_curve_stats[:][stat.loss_type] = curves
            if oq.insured_losses:
                ins_curve_stats[:][stat.loss_type] = ins_curves
            if oq.conditional_loss_poes:
                loss_map_stats[:][stat.loss_type] = maps

        for i, stats in enumerate(_mean_quantiles(oq.quantile_loss_curves)):
            self.store(loss_curve_key, stats, loss_curve_stats[i])
            if oq.insured_losses:
                self.store(loss_curve_key + '_ins', stats, ins_curve_stats[i])
            if oq.conditional_loss_poes:
                self.store(loss_curve_key + '_maps', stats, loss_map_stats[i])
