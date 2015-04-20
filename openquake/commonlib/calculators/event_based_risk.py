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

from openquake.baselib.general import AccumDict
from openquake.commonlib.calculators import base
from openquake.commonlib import readinput, writers, parallel
from openquake.risklib import riskinput, scientific


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
            for tag, losses, ins_losses in zip(
                    out.tags, out.event_loss_per_asset,
                    out.insured_loss_per_asset):
                data = [(asset.id, loss, ins_loss)
                        for asset, loss, ins_loss in zip(
                            out.assets, losses, ins_losses)
                        if loss and asset.id in specific]
                acc[out.hid, out.loss_type] += {
                    tag: AccumDict(
                        data=data, loss=sum(losses), ins_loss=sum(ins_losses),
                        nonzero=sum(1 for loss in losses if loss),
                        total=len(losses))}
    return acc


@base.calculators.add('event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
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
            gsims_by_trt_id, oq.truncation_level, correl_model, eps_dict,
            oq.concurrent_tasks or 1))
        logging.info('Built %d risk inputs', len(self.riskinputs))

    def post_execute(self, result):
        """
        Extract from the result dictionary
        (rlz.ordinal, loss_type) -> tag -> [(asset.id, loss), ...]
        several interesting outputs.
        """
        oq = self.oqparam
        self.asset_dict = {
            a.id: a for assets in self.assets_by_site for a in assets
            if a.id in self.oqparam.specific_assets}
        self.risk_out['specific_assets'] = specific_assets = [
            self.asset_dict[a] for a in sorted(self.oqparam.specific_assets)]
        self.saved = AccumDict()
        for ordinal, loss_type in sorted(result):
            data = result[ordinal, loss_type]
            # asset_ref -> [(tag, loss, ins_loss), ...]
            elass = {asset.id: [] for asset in specific_assets}
            elagg = []  # aggregate event loss
            nonzero = total = 0
            for tag in sorted(data):
                d = data[tag]
                for asset_ref, loss, ins_loss in sorted(d['data']):
                    elass[asset_ref].append((tag, loss, ins_loss))
                elagg.append((tag, d['loss'], d['ins_loss']))  # aggregates
                nonzero += d['nonzero']
                total += d['total']
            logging.info('rlz=%d, loss type=%s: %d/%d nonzero losses',
                         ordinal, loss_type, nonzero, total)
            if elass:
                key = 'rlz-%03d-%s-event-loss-asset' % (ordinal, loss_type)
                data = []
                for asset_ref, rows in elass.iteritems():
                    for tag, loss, ins_loss in rows:
                        data.append((tag, asset_ref, loss, ins_loss))
                self.export_csv(key, data)

                # build the loss curves per asset
                key = 'rlz-%03d-%s-loss-curves' % (ordinal, loss_type)
                self.risk_out[key] = lc = self.build_loss_curves(elass, 1)
                data = []
                for asset, (losses, poes), avg in zip(
                        specific_assets, lc['losses_poes'], lc['avg']):
                    data.append((asset.id, losses, poes, avg))
                self.export_csv(key, data)

                if oq.insured_losses:
                    # build the insured loss curves per asset
                    key_ins = 'rlz-%03d-%s-ins-loss-curves' % (
                        ordinal, loss_type)
                    self.risk_out[key_ins] = ic = self.build_loss_curves(
                        elass, 2)
                    data = []
                    for asset, (losses, poes), avg in zip(
                            specific_assets, ic['losses_poes'], ic['avg']):
                        data.append((asset.id, losses, poes, avg))
                    self.export_csv(key_ins, data)

                if oq.conditional_loss_poes:
                    # build the loss maps per asset an array of shape (P, S)
                    key_map = 'rlz-%03d-%s-loss-maps' % (ordinal, loss_type)
                    self.risk_out[key_map] = scientific.loss_map_matrix(
                        oq.conditional_loss_poes,
                        self.risk_out[key]['losses_poes'])
                    data = []
                    for asset, loss in zip(
                            specific_assets, self.risk_out[key_map]):
                        data.append((asset.id, loss))
                    self.export_csv(key_map, data)

            if elagg:
                key = 'rlz-%03d-%s-event-loss' % (ordinal, loss_type)
                self.export_csv(key, elagg)

                # aggregate loss curve for all tags
                key = 'rlz-%03d-%s-agg-loss-curve' % (ordinal, loss_type)
                losses, poes, avg, map_ = self.build_agg_loss_curve_and_map(
                    [loss for _tag, loss, _ins_loss in elagg])
                self.risk_out[key] = dict(losses=losses, poes=poes, avg=avg)
                self.export_csv(key, [('aggregate', losses, poes, avg)])

        # export statistics (i.e. mean and quantiles) for curves and maps
        if len(self.rlzs_assoc.realizations) > 1:
            for stat in self.calc_stats():  # one stat for each loss_type
                curves, ins_curves, maps = scientific.get_stat_curves(stat)
                key = 'loss_curve_stats-%s' % stat.loss_type
                self.export_csv(key, curves)
                if oq.insured_losses:
                    key = 'ins_loss_curve_stats-%s' % stat.loss_type
                    self.export_csv(key, ins_curves)
                if oq.conditional_loss_poes:
                    key = 'loss_map_stats-%s' % stat.loss_type
                    self.export_csv(key, maps)
        return self.saved

    def build_agg_loss_curve_and_map(self, losses):
        """
        Build a loss curve from a set of losses with length give by
        the parameter loss_curve_resolution.

        :returns: a pair (losses, poes)
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

    def build_loss_curves(self, elass, i):
        """
        Build loss curves per asset from a set of losses with length given by
        the parameter loss_curve_resolution.

        :returns: a pair (losses, poes)
        """
        # elass has the form (tag, asset_ref, loss, ins_loss)
        # i is an index 1 (loss curves) or 2 (insured losses)
        oq = self.oqparam
        R = oq.loss_curve_resolution
        loss_curve_dt = numpy.dtype(
            [('losses_poes', (float, (2, R))), ('avg', float)])

        lcs = []
        for asset in self.risk_out['specific_assets']:
            all_losses = [loss[i] for loss in elass[asset.id]]
            if all_losses:
                losses_poes = scientific.event_based(
                    all_losses, tses=oq.tses, time_span=oq.investigation_time,
                    curve_resolution=R)
                avg = scientific.average_loss(losses_poes)
            else:
                losses_poes = numpy.zeros((2, R))
                avg = 0
            lcs.append((losses_poes, avg))

        return numpy.array(lcs, loss_curve_dt)

    def extract_loss_curve_outputs(self, loss_type):
        """
        Extract the loss curve outputs from the .risk_out dictionary.
        Used to compute the statistics.
        """
        rlzs = self.rlzs_assoc.realizations
        assets = self.risk_out['specific_assets']
        for key in self.risk_out:
            mo = re.match('rlz-(\d+)-%s-loss-curves' % loss_type, key)
            if mo:
                ordinal = int(mo.group(1))
                weight = rlzs[ordinal].weight
                lcs = self.risk_out[key]
                out = scientific.Output(
                    assets, loss_type, ordinal, weight,
                    loss_curves=lcs['losses_poes'], insured_curves=None)
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
            if outputs:
                yield stats.build(outputs)
            else:
                # this should never happen
                logging.error('No outputs found for loss_type=%s', loss_type)

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
        header = loss_curves_per_asset[0]._fields
        key = 'loss_curve_stats-%s' % loss_type
        self.export_csv(key, [header] + loss_curves_per_asset)

    def export_curves_compact(self, loss_curves_per_asset, loss_type):
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
            lon, lat = lca.asset.location
            data.append((lon, lat, lca.asset.id, lca.asset.value(loss_type),
                         lca.average_loss, '', loss_type))
        header = ['lon', 'lat', 'asset_ref', 'asset_value', 'average_loss',
                  'stddev_loss', 'loss_type']
        key = 'loss_avg_stats-%s' % loss_type
        self.export_csv(key, [header] + data)

    def export_maps_compact(self, loss_maps_per_asset, loss_type):
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
            lon, lat = lma.asset.location
            data.append((lon, lat, lma.asset.id, lma.loss, loss_type))

        header = ['lon', 'lat', 'asset_ref', 'average_loss', 'loss_type']
        key = 'loss_map_stats-%s' % loss_type
        self.export_csv(key, [header] + data)

    def export_csv(self, key, data):
        if not data:
            return
        dest = os.path.join(self.oqparam.export_dir, key) + '.csv'
        if key.startswith('rlz-') and not self.oqparam.individual_curves:
            return  # don't export individual curves
        if hasattr(data[0], '_fields'):
            header = [data[0]._fields]
        else:
            header = []
        writers.save_csv(dest, header + data, fmt='%10.6E')
        self.saved[key] = dest
        return dest
