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

import os.path
import logging
import operator
import collections

from openquake.baselib.general import AccumDict
from openquake.commonlib.calculators import base
from openquake.commonlib import readinput, writers
from openquake.risklib import riskinput, workflows


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
    for out_by_rlz in riskmodel.gen_outputs(
            riskinputs, rlzs_assoc, monitor):
        for rlz, out in out_by_rlz.iteritems():
            for tag, losses in zip(out.tags, out.event_loss_per_asset):
                pairs = [(asset.id, loss) for asset, loss in zip(
                    out.assets, losses) if loss and asset.id in specific]
                acc[rlz.ordinal, out.loss_type] += {
                    tag: AccumDict(
                        pairs=pairs, loss=sum(losses), nonzero=len(pairs),
                        total=sum(1 for a in out.assets if a.id in specific))}
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
        oq.tses = oq.investigation_time * oq.ses_per_logic_tree_path * (
            oq.number_of_logic_tree_samples or 1)

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
        self.riskinputs = []
        for trt_id, sesruptures in sorted(
                haz_out['ruptures_by_trt'].iteritems()):
            # there should be different epsilons for each SES collection
            # and for each taxonomy
            eps_dict = riskinput.make_eps_dict(
                self.assets_by_site,
                min(len(sesruptures), epsilon_sampling),
                getattr(oq, 'master_seed', 42),
                getattr(oq, 'asset_correlation', 0))

            gsims = gsims_by_trt_id[trt_id]

            sesruptures.sort(key=operator.attrgetter('tag'))
            ris = self.riskmodel.build_inputs_from_ruptures(
                self.sitecol, self.assets_by_site, sesruptures,
                gsims, oq.truncation_level, correl_model, eps_dict,
                epsilon_sampling)

            self.riskinputs.extend(ris)
        logging.info('Built %d risk inputs', len(self.riskinputs))

    def post_execute(self, result):
        saved = {}
        for ordinal, loss_type in sorted(result):
            data = result[ordinal, loss_type]
            ela = []  # event loss per asset
            elo = []  # total event loss
            nonzero = total = 0
            for tag in sorted(data):
                d = data[tag]
                for asset_id, loss in sorted(d['pairs']):
                    ela.append((tag, asset_id, loss))
                elo.append((tag, d['loss']))
                nonzero += d['nonzero']
                total += d['total']
            if ela:
                key = 'rlz-%03d-%s-event-loss-asset' % (ordinal, loss_type)
                saved[key] = self.export_csv(key, ela)
                logging.info('rlz %d, loss type %s: %d/%d nonzero losses',
                             ordinal, loss_type, nonzero, total)
            if elo:
                key = 'rlz-%03d-%s-event-loss' % (ordinal, loss_type)
                saved[key] = self.export_csv(key, elo)
        return saved

    def export_csv(self, key, data):
        dest = os.path.join(self.oqparam.export_dir, key) + '.csv'
        return writers.save_csv(dest, data, fmt='%11.8E')
