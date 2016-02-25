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

from openquake.baselib.general import AccumDict
from openquake.calculators import base, event_based_risk as ebr
from openquake.commonlib import readinput, parallel
from openquake.risklib import riskinput
from openquake.commonlib.parallel import apply_reduce

U32 = numpy.uint32
F32 = numpy.float32


@parallel.litetask
def eb_risk(riskinputs, riskmodel, rlzs_assoc, assets_by_site, monitor):
    """
    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
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
    I = monitor.I
    L, R = len(lti), len(rlzs_assoc.realizations)
    ela_dt = numpy.dtype([('rup_id', U32), ('ass_id', U32),
                          ('loss', (F32, L * I))])
    elt_dt = numpy.dtype([('rup_id', U32), ('loss', (F32, L * I))])

    result = {}
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
                        loss2 = (groundloss, insuredloss)
                        ass_losses.append((r, rup_id, aid, l, loss2))
    ass_losses.sort()

    # ASSLOSS
    items = [[] for _ in range(R)]
    for (r, rid, aid), group in itertools.groupby(
            ass_losses, operator.itemgetter(0, 1, 2)):
        loss = numpy.zeros(L * I, F32)
        for _r, _rid, _aid, l, loss2 in group:
            loss[l] = loss2[0]
            if I == 2:
                loss[L + l] = loss2[1]
        items[r].append((rid, aid, loss))
    for r in range(R):
        items[r] = numpy.array(items[r], ela_dt)
    result['ASSLOSS'] = items

    # AGGLOSS
    items = [[] for _ in range(R)]
    for (r, rid), group in itertools.groupby(
            ass_losses, operator.itemgetter(0, 1)):
        loss = numpy.zeros(L * I, F32)
        for _r, _rid, _aid, l, loss2 in group:
            loss[l] += loss2[0]
            if I == 2:
                loss[l + L] += loss2[1]
        items[r].append((rid, loss))
    for r in range(R):
        items[r] = numpy.array(items[r], elt_dt)
    result['AGGLOSS'] = items
    return result


@base.calculators.add('eb_risk')
class EBRiskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the event loss table only
    """
    pre_calculator = 'event_based_rupture'
    core_task = eb_risk
    is_stochastic = True

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some datasets in the datastore.
        """
        super(EBRiskCalculator, self).pre_execute()
        if not self.riskmodel:  # there is no riskmodel, exit early
            self.execute = lambda: None
            self.post_execute = lambda result: None
            return
        oq = self.oqparam
        correl_model = readinput.get_correl_model(oq)
        gsims_by_col = self.rlzs_assoc.get_gsims_by_col()

        logging.info('Populating the risk inputs')
        rup_by_tag = AccumDict()
        for colkey in self.datastore['sescollection']:
            rup_by_tag += self.datastore['sescollection/' + colkey]
        all_ruptures = [rup_by_tag[tag] for tag in sorted(rup_by_tag)]
        for i, rup in enumerate(all_ruptures):
            rup.ordinal = i
        self.N = len(self.assetcol)
        self.E = len(all_ruptures)
        if not self.riskmodel.covs:
            # do not generate epsilons
            eps = ebr.FakeMatrix(self.N, self.E)
        else:
            eps = riskinput.make_eps(
                self.assets_by_site, self.E, oq.master_seed,
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
        self.monitor.I = I = self.oqparam.insured_losses + 1

        self.N = len(self.assetcol)
        self.E = len(self.datastore['tags'])

        ela_dt = numpy.dtype([('rup_id', U32), ('ass_id', U32),
                              ('loss', (F32, L * I))])
        self.asset_loss_table = [None] * R
        self.agg_loss_table = [None] * R

        self.elt_dt = numpy.dtype([('rup_id', U32), ('loss', (F32, L * I))])
        for rlz in self.rlzs_assoc.realizations:
            self.asset_loss_table[rlz.ordinal] = self.datastore.create_dset(
                'asset_loss_table/rlz-%03d' % rlz.ordinal, ela_dt)
            self.agg_loss_table[rlz.ordinal] = self.datastore.create_dset(
                'agg_loss_table/rlz-%03d' % rlz.ordinal, self.elt_dt)

    def execute(self):
        """
        Run the event_based_risk calculator and aggregate the results
        """
        self.saved = collections.Counter()  # nbytes per HDF5 key
        self.ass_bytes = 0
        self.agg_bytes = 0
        rlz_ids = getattr(self.oqparam, 'rlz_ids', ())
        if rlz_ids:
            self.rlzs_assoc = self.rlzs_assoc.extract(rlz_ids)
        return apply_reduce(
            self.core_task.__func__,
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
        for i, rlz in enumerate(self.realizations):
            elt = self.datastore['asset_loss_table/rlz-%03d' % i]
            alt = self.datastore['agg_loss_table/rlz-%03d' % i]
            elt.attrs['nonzero_fraction'] = len(elt) / (self.N * self.E)
            alt.attrs['nonzero_fraction'] = len(alt) / self.N

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
