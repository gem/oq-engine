# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import logging
import operator
import numpy

from openquake.baselib.general import AccumDict, group_array
from openquake.baselib.python3compat import zip, encode
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.hazardlib.calc.stochastic import TWO32
from openquake.risklib import riskinput, riskmodels
from openquake.calculators import base
from openquake.calculators.export.loss_curves import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64
getweight = operator.attrgetter('weight')


def build_loss_tables(dstore):
    """
    Compute the total losses by rupture and losses by rlzi.
    """
    oq = dstore['oqparam']
    L = len(oq.loss_dt().names)
    R = dstore['csm_info'].get_num_rlzs()
    serials = dstore['ruptures']['serial']
    idx_by_ser = dict(zip(serials, range(len(serials))))
    tbl = numpy.zeros((len(serials), L), F32)
    lbr = numpy.zeros((R, L), F32)  # losses by rlz
    for rec in dstore['losses_by_event'].value:  # call .value for speed
        idx = idx_by_ser[rec['eid'] // TWO32]
        tbl[idx] += rec['loss']
        lbr[rec['rlzi']] += rec['loss']
    return tbl, lbr


def event_based_risk(riskinputs, riskmodel, param, monitor):
    """
    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        a dictionary of parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary of numpy arrays of shape (L, R)
    """
    L = len(riskmodel.lti)
    epspath = param['epspath']
    for ri in riskinputs:
        with monitor('getting hazard'):
            ri.hazard_getter.init()
            hazard = ri.hazard_getter.get_hazard()
        mon = monitor('build risk curves', measuremem=False)
        A = len(ri.aids)
        R = ri.hazard_getter.num_rlzs
        try:
            avg = numpy.zeros((A, R, L), F32)
        except MemoryError:
            raise MemoryError(
                'Building array avg of shape (%d, %d, %d)' % (A, R, L))
        result = dict(aids=ri.aids, avglosses=avg)
        acc = AccumDict()  # accumulator eidx -> agglosses
        aid2idx = {aid: idx for idx, aid in enumerate(ri.aids)}
        if 'builder' in param:
            builder = param['builder']
            P = len(builder.return_periods)
            all_curves = numpy.zeros((A, R, P), builder.loss_dt)
        # update the result dictionary and the agg array with each output
        for out in riskmodel.gen_outputs(ri, monitor, epspath, hazard):
            if len(out.eids) == 0:  # this happens for sites with no events
                continue
            r = out.rlzi
            agglosses = numpy.zeros((len(out.eids), L), F32)
            for l, loss_type in enumerate(riskmodel.loss_types):
                loss_ratios = out[loss_type]
                if loss_ratios is None:  # for GMFs below the minimum_intensity
                    continue
                avalues = riskmodels.get_values(loss_type, ri.assets)
                for a, asset in enumerate(ri.assets):
                    aval = avalues[a]
                    aid = asset['ordinal']
                    idx = aid2idx[aid]
                    ratios = loss_ratios[a]  # length E

                    # average losses
                    avg[idx, r, l] = (
                        ratios.sum(axis=0) * param['ses_ratio'] * aval)

                    # agglosses
                    agglosses[:, l] += ratios * aval
                    if 'builder' in param:
                        with mon:  # this is the heaviest part
                            all_curves[idx, r][loss_type] = (
                                builder.build_curve(aval, ratios, r))

            # NB: I could yield the agglosses per output, but then I would
            # have millions of small outputs with big data transfer and slow
            # saving time
            acc += dict(zip(out.eids, agglosses))

        if 'builder' in param:
            clp = param['conditional_loss_poes']
            result['curves-rlzs'], result['curves-stats'] = builder.pair(
                all_curves, param['stats'])
            if R > 1 and param['individual_curves'] is False:
                del result['curves-rlzs']
            if clp:
                result['loss_maps-rlzs'], result['loss_maps-stats'] = (
                    builder.build_maps(all_curves, clp, param['stats']))
                if R > 1 and param['individual_curves'] is False:
                    del result['loss_maps-rlzs']

        # store info about the GMFs, must be done at the end
        result['agglosses'] = (numpy.array(list(acc)),
                               numpy.array(list(acc.values())))
        yield result


@base.calculators.add('event_based_risk')
class EbrCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the total losses by taxonomy
    """
    core_task = event_based_risk
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['event_based', 'event_based_risk', 'ucerf_hazard',
                      'ebrisk']

    def pre_execute(self):
        oq = self.oqparam
        super().pre_execute()
        parent = self.datastore.parent
        if not self.oqparam.ground_motion_fields:
            return  # this happens in the reportwriter

        self.L = len(self.riskmodel.lti)
        self.T = len(self.assetcol.tagcol)
        self.A = len(self.assetcol)
        if parent:
            self.datastore['csm_info'] = parent['csm_info']
            self.events = parent['events'].value[['id', 'rlz']]
        else:
            self.events = self.datastore['events'].value[['id', 'rlz']]
        if oq.return_periods != [0]:
            # setting return_periods = 0 disable loss curves and maps
            eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
            if eff_time < 2:
                logging.warning(
                    'eff_time=%s is too small to compute loss curves',
                    eff_time)
            else:
                self.param['builder'] = get_loss_builder(
                    parent if parent else self.datastore,
                    oq.return_periods, oq.loss_dt())
        # sorting the eids is essential to get the epsilons in the right
        # order (i.e. consistent with the one used in ebr from ruptures)
        self.riskinputs = self.build_riskinputs('gmf')
        self.param['epspath'] = riskinput.cache_epsilons(
            self.datastore, oq, self.assetcol, self.riskmodel, self.E)
        self.param['avg_losses'] = oq.avg_losses
        self.param['ses_ratio'] = oq.ses_ratio
        self.param['stats'] = list(oq.hazard_stats().items())
        self.param['conditional_loss_poes'] = oq.conditional_loss_poes
        self.taskno = 0
        self.start = 0
        avg_losses = oq.avg_losses
        if avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, self.R, self.L))
        self.agglosses = numpy.zeros((self.E, self.L), F32)
        if 'builder' in self.param:
            logging.warning(
                'Building the loss curves and maps for each asset is '
                'deprecated: consider building the aggregate curves and '
                'maps with the ebrisk calculator instead')
            self.build_datasets(self.param['builder'])
        if parent:
            parent.close()  # avoid concurrent reading issues

    def build_datasets(self, builder):
        oq = self.oqparam
        R = len(builder.weights)
        stats = self.param['stats']
        A = self.A
        S = len(stats)
        P = len(builder.return_periods)
        C = len(self.oqparam.conditional_loss_poes)
        L = self.L
        self.loss_maps_dt = (F32, (C, L))
        if oq.individual_curves or R == 1:
            self.datastore.create_dset('curves-rlzs', F32, (A, R, P, L))
            self.datastore.set_attrs(
                'curves-rlzs', return_periods=builder.return_periods)
        if oq.conditional_loss_poes:
            self.datastore.create_dset(
                'loss_maps-rlzs', self.loss_maps_dt, (A, R), fillvalue=None)
        if R > 1:
            self.datastore.create_dset('curves-stats', F32, (A, S, P, L))
            self.datastore.set_attrs(
                'curves-stats', return_periods=builder.return_periods,
                stats=[encode(name) for (name, func) in stats])
            if oq.conditional_loss_poes:
                self.datastore.create_dset(
                    'loss_maps-stats', self.loss_maps_dt, (A, S),
                    fillvalue=None)
                self.datastore.set_attrs(
                    'loss_maps-stats',
                    stats=[encode(name) for (name, func) in stats])

    def save_losses(self, dic):
        """
        Save the event loss tables incrementally.

        :param dic:
            dictionary with agglosses, avglosses
        """
        idxs, agglosses = dic.pop('agglosses')
        if len(idxs):
            self.agglosses[idxs] += agglosses
        aids = dic.pop('aids')
        if self.oqparam.avg_losses:
            self.dset[aids, :, :] = dic.pop('avglosses')
        self._save_curves(dic, aids)
        self._save_maps(dic, aids)
        self.taskno += 1

    def _save_curves(self, dic, aids):
        for key in ('curves-rlzs', 'curves-stats'):
            array = dic.get(key)  # shape (A, S, P)
            if array is not None:
                shp = array.shape + (self.L,)
                self.datastore[key][aids, ...] = array.view(F32).reshape(shp)

    def _save_maps(self, dic, aids):
        for key in ('loss_maps-rlzs', 'loss_maps-stats'):
            array = dic.get(key)  # shape (A, S, C, LI)
            if array is not None:
                self.datastore[key][aids, ...] = array

    def combine(self, dummy, res):
        """
        :param dummy: unused parameter
        :param res: a result dictionary
        """
        with self.monitor('saving losses', measuremem=True):
            self.save_losses(res)
        return 1

    def post_execute(self, result):
        """
        Save risk data and build the aggregate loss curves
        """
        logging.info('Saving event loss table')
        elt_dt = numpy.dtype(
            [('eid', U64), ('rlzi', U16), ('loss', (F32, (self.L,)))])
        with self.monitor('saving event loss table', measuremem=True):
            agglosses = numpy.fromiter(
                ((eid, rlz, losses)
                 for (eid, rlz), losses in zip(self.events, self.agglosses)
                 if losses.any()), elt_dt)
            self.datastore['losses_by_event'] = agglosses
            loss_types = ' '.join(self.oqparam.loss_dt().names)
            self.datastore.set_attrs('losses_by_event', loss_types=loss_types)
        self.postproc()

    def postproc(self):
        """
        Build aggregate loss curves in process
        """
        dstore = self.datastore
        self.before_export()  # set 'realizations'
        oq = self.oqparam
        stats = self.param['stats']
        # store avg_losses-stats
        if oq.avg_losses:
            set_rlzs_stats(self.datastore, 'avg_losses')
        try:
            b = self.param['builder']
        except KeyError:  # don't build auxiliary tables
            return
        if dstore.parent:
            dstore.parent.open('r')  # to read the ruptures
        if 'ruptures' in self.datastore and len(self.datastore['ruptures']):
            logging.info('Building loss tables')
            with self.monitor('building loss tables', measuremem=True):
                rlt, lbr = build_loss_tables(dstore)
                dstore['rup_loss_table'] = rlt
                dstore['losses_by_rlzi'] = lbr
                ridx = [rlt[:, lti].argmax() for lti in range(self.L)]
                dstore.set_attrs('rup_loss_table', ridx=ridx)
        logging.info('Building aggregate loss curves')
        with self.monitor('building agg_curves', measuremem=True):
            lbr = group_array(dstore['losses_by_event'].value, 'rlzi')
            dic = {r: arr['loss'] for r, arr in lbr.items()}
            array, arr_stats = b.build(dic, stats)
        loss_types = ' '.join(self.oqparam.loss_dt().names)
        units = self.assetcol.cost_calculator.get_units(loss_types.split())
        if oq.individual_curves or self.R == 1:
            self.datastore['agg_curves-rlzs'] = array
            self.datastore.set_attrs(
                'agg_curves-rlzs',
                return_periods=b.return_periods,
                loss_types=loss_types, units=units)
        if arr_stats is not None:
            self.datastore['agg_curves-stats'] = arr_stats
            self.datastore.set_attrs(
                'agg_curves-stats', return_periods=b.return_periods,
                stats=[encode(name) for (name, func) in stats],
                loss_types=loss_types, units=units)
