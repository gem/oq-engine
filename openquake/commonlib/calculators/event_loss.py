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

import re
import os.path
import logging
import operator
import collections

import numpy

from openquake.baselib.general import AccumDict, groupby
from openquake.commonlib.calculators import base
from openquake.commonlib import readinput, writers, parallel
from openquake.risklib import riskinput, workflows, scientific


@parallel.litetask
def event_loss(riskinputs, riskmodel, rlzs_assoc, monitor):
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
        a dictionary (rlz.ordinal, loss_type) -> tag -> [(asset.id, loss), ...]
    """
    specific = riskmodel.specific_assets
    acc = collections.defaultdict(AccumDict)
    # rlz.ordinal, loss_type -> tag -> [(asset.id, loss), ...]
    for out_by_rlz in riskmodel.gen_outputs(riskinputs, rlzs_assoc, monitor):
        for out in out_by_rlz:
            for tag, losses in zip(out.tags, out.event_loss_per_asset):
                pairs = [(asset.id, loss) for asset, loss in zip(
                    out.assets, losses) if loss and asset.id in specific]
                acc[out.hid, out.loss_type] += {
                    tag: AccumDict(
                        pairs=pairs, loss=sum(losses),
                        nonzero=sum(1 for loss in losses if loss),
                        total=len(losses))}
    return acc


# hack: temporarily 'event_based_risk' is an alias for 'event_loss'
@base.calculators.add('event_loss', 'event_based_risk')
class EventLossCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    hazard_calculator = 'event_based_rupture'
    core_func = event_loss
    result_kind = 'event_loss_by_rlz_tag'

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
        oq = self.oqparam
        epsilon_sampling = getattr(oq, 'epsilon_sampling', 1000)

        # HACK: replace the event_based_risk workflow with the event_loss
        # workflow, so that the riskmodel has the correct workflows
        workflows.registry['event_based_risk'] = workflows.registry[
            'event_loss']
        self.riskmodel = readinput.get_risk_model(self.oqparam)
        self.riskmodel.specific_assets = set(self.oqparam.specific_assets)

        haz_out, hcalc = base.get_hazard(self)

        self.assets_by_site = hcalc.assets_by_site
        self.composite_source_model = hcalc.composite_source_model
        self.sitecol = hcalc.sitecol
        self.rlzs_assoc = hcalc.rlzs_assoc

        correl_model = readinput.get_correl_model(oq)
        gsims_by_trt_id = self.rlzs_assoc.get_gsims_by_trt_id()
        logging.info('Building the epsilons')

        logging.info('Populating the risk inputs')
        all_ruptures = sum(
            (rups for rups in haz_out['ruptures_by_trt'].itervalues()), [])
        all_ruptures.sort(key=operator.attrgetter('tag'))
        num_samples = min(len(all_ruptures), epsilon_sampling)
        eps_dict = riskinput.make_eps_dict(
            self.assets_by_site, num_samples,
            getattr(oq, 'master_seed', 42),
            getattr(oq, 'asset_correlation', 0))
        logging.info('Generated %d epsilons', num_samples * len(eps_dict))
        self.riskinputs = list(self.riskmodel.build_inputs_from_ruptures(
            self.sitecol, self.assets_by_site, all_ruptures,
            gsims_by_trt_id, oq.truncation_level, correl_model, eps_dict, 32))
        # we try to generate 32 tasks; this is ad hoc and will change
        logging.info('Built %d risk inputs', len(self.riskinputs))

    def post_execute(self, result):
        """
        Extract from the result dictionary
        (rlz.ordinal, loss_type) -> tag -> [(asset.id, loss), ...]
        several interesting outputs.
        """
        self.asset_dict = {a.id: a for assets in self.assets_by_site
                           for a in assets}
        saved = AccumDict()
        total_losses = []
        for ordinal, loss_type in sorted(result):
            data = result[ordinal, loss_type]
            elass = []  # event loss per asset
            elagg = []  # aggregate event loss
            nonzero = total = 0
            for tag in sorted(data):
                d = data[tag]
                for asset_ref, loss in sorted(d['pairs']):
                    elass.append((tag, asset_ref, loss))
                elagg.append((tag, d['loss']))  # sum of the losses
                nonzero += d['nonzero']
                total += d['total']
            logging.info('rlz=%d, loss type=%s: %d/%d nonzero losses',
                         ordinal, loss_type, nonzero, total)

            if elass:
                key = 'rlz-%03d-%s-event-loss-asset' % (ordinal, loss_type)
                saved[key] = self.export_csv(key, elass)

                # aggregate loss curves per asset
                losses_by_asset = groupby(  # (tag, asset_ref, loss) triples
                    elass, operator.itemgetter(1),
                    lambda rows: [row[2] for row in rows])
                key = 'rlz-%03d-%s-loss-curves' % (ordinal, loss_type)
                key_map = 'rlz-%03d-%s-loss-maps' % (ordinal, loss_type)
                self.risk_out[key] = []
                self.risk_out[key_map] = maps = []
                for asset_ref, all_losses in losses_by_asset.iteritems():
                    losses, poes, avg, maps_ = (
                        self.build_loss_curve_and_maps(all_losses))
                    lca = scientific.LossCurvePerAsset(
                        asset_ref, losses, poes, avg)
                    # since we are considering a single asset, maps_
                    # has shape (P, 1) where P = #conditional_loss_poes
                    lma = [asset_ref] + [loss for loss, in maps_]
                    self.risk_out[key].append(lca)
                    self.risk_out[key_map].append(lma)
                saved[key] = self.export_csv(key, self.risk_out[key])
                if maps:
                    saved[key_map] = self.export_csv(key_map, maps)

            if elagg:
                key = 'rlz-%03d-%s-event-loss' % (ordinal, loss_type)
                saved[key] = self.export_csv(key, elagg)
                # aggregate loss curve for all tags
                key = 'rlz-%03d-%s-agg-loss-curve' % (ordinal, loss_type)
                losses, poes, avg, maps = self.build_loss_curve_and_maps(
                    [loss for _tag, loss in elagg])
                self.risk_out[key] = dict(losses=losses, poes=poes, avg=avg)
                total_losses.append((ordinal, loss_type, avg))
                saved[key] = self.export_csv(
                    key, [('aggregate', losses, poes, avg)])

        header = 'rlz_no loss_type avg_loss stddev'.split()
        saved['total-losses'] = self.export_csv(
            'total-losses', [header] + total_losses)

        if len(self.rlzs_assoc.realizations) > 1:
            for stats in self.calc_stats():
                curves, ins_curves = scientific.get_stat_curves(stats)
                saved += self.export_curves_stats(curves, loss_type)
                if ins_curves:
                    saved += self.export_curves_stats(ins_curves, loss_type)
                maps = scientific.get_stat_maps(stats)
                saved += self.export_maps(maps, loss_type)
        return saved

    def build_loss_curve_and_maps(self, losses):
        """
        Build a loss curve from a set of losses with length give by
        the parameter loss_curve_resolution.

        :returns: a pair (losses, poes)
        """
        oq = self.oqparam
        losses_poes = scientific.event_based(
            losses, tses=oq.tses, time_span=oq.investigation_time,
            curve_resolution=oq.loss_curve_resolution)
        loss_maps = scientific.loss_map_matrix(
            oq.conditional_loss_poes, [losses_poes])
        return (losses_poes[0], losses_poes[1],
                scientific.average_loss(losses_poes), loss_maps)

    def extract_loss_curve_outputs(self, loss_type):
        """
        Extract the loss curve outputs from the .risk_out dictionary.
        Used to compute the statistics.
        """
        rlzs = self.rlzs_assoc.realizations
        for key in self.risk_out:
            mo = re.match('rlz-(\d+)-%s-loss-curves' % loss_type, key)
            if mo:
                ordinal = int(mo.group(1))
                weight = rlzs[ordinal].weight
                out = scientific.Output(
                    [], loss_type, ordinal, weight,
                    loss_curves=[], insured_curves=None)
                for lca in self.risk_out[key]:
                    out.assets.append(lca.asset_ref)
                    out.loss_curves.append((lca.losses, lca.poes))
                yield out

    def calc_stats(self):
        """
        Compute all statistics starting from the loss curves for each asset.
        Yield a statistical output object for each loss type.
        """
        oq = self.oqparam
        stats = scientific.StatsBuilder(
            oq.quantile_loss_curves, oq.conditional_loss_poes, [],
            scientific.normalize_curves_eb)
        for loss_type in self.riskmodel.get_loss_types():
            outputs = list(self.extract_loss_curve_outputs(loss_type))
            yield stats.build(outputs)

    # should be done only on demand
    def export_curves_stats(self, loss_curves_per_asset, loss_type):
        """
        Export the mean and quantile loss curves in CSV format

        :param loss_curves_per_asset:
            a list of LossCurvePerAsset instance of homogeneous kind
        :param loss_type:
            the loss type
        :returns:
            a dictionary key -> path of the exported file
        """
        data = []
        for lca in loss_curves_per_asset:
            asset = self.asset_dict[lca.asset_ref]
            lon, lat = asset.location
            data.append((lon, lat, asset.id, asset.value(loss_type),
                         lca.average_loss, '', loss_type))
        header = ['lon', 'lat', 'asset_ref', 'asset_value', 'average_loss',
                  'stddev_loss', 'loss_type']
        key = 'loss_curve_stats-%s' % loss_type
        return {key: self.export_csv('loss_curve_stats', [header] + data)}

    def export_maps(self, loss_maps_per_asset, loss_type):
        """
        Export the mean and quantile loss maps in CSV format

        :param loss_maps_per_asset:
            a list of LossMapPerAsset instances of homogeneous kind
        :param loss_type:
            the loss type
        :returns:
            a dictionary key -> path of the exported file
        """
        data = []
        for lma in loss_maps_per_asset:
            asset = self.asset_dict[lma.asset_ref]
            lon, lat = asset.location
            data.append((lon, lat, lma.asset_ref, lma.loss, loss_type))
        header = ['lon', 'lat', 'asset_ref', 'average_loss', 'loss_type']
        key = 'loss_map_stats-%s' % loss_type
        return {key: self.export_csv('loss_map_stats', [header] + data)}

    def export_csv(self, key, data):
        dest = os.path.join(self.oqparam.export_dir, key) + '.csv'
        return writers.save_csv(dest, data, fmt='%10.6E')
