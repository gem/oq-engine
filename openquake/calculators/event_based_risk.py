# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
import itertools
import collections
import numpy

from openquake.baselib.python3compat import zip, encode
from openquake.baselib.general import AccumDict, split_in_blocks
from openquake.baselib import parallel
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import riskinput
from openquake.calculators import base, event_based, getters
from openquake.calculators.export.loss_curves import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64
getweight = operator.attrgetter('weight')
indices_dt = numpy.dtype([('start', U32), ('stop', U32)])


def build_loss_tables(dstore):
    """
    Compute the total losses by rupture and losses by rlzi.
    """
    oq = dstore['oqparam']
    L = len(oq.loss_dt().names)
    R = dstore['csm_info'].get_num_rlzs()
    events = dstore['events']
    serials = dstore['ruptures']['serial']
    rup_by_eid = dict(zip(events['eid'], events['rup_id']))
    idx_by_ser = dict(zip(serials, range(len(serials))))
    tbl = numpy.zeros((len(serials), L), F32)
    lbr = numpy.zeros((R, L), F32)  # losses by rlz
    for rec in dstore['losses_by_event'].value:  # call .value for speed
        rupid = rup_by_eid[rec['eid']]
        tbl[idx_by_ser[rupid]] += rec['loss']
        lbr[rec['rlzi']] += rec['loss']
    return tbl, lbr


def event_based_risk(riskinput, riskmodel, param, monitor):
    """
    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        a dictionary of parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary of numpy arrays of shape (L, R)
    """
    with monitor('%s.init' % riskinput.hazard_getter.__class__.__name__):
        riskinput.hazard_getter.init()
    eids = riskinput.hazard_getter.eids
    A = len(riskinput.aids)
    E = len(eids)
    I = param['insured_losses'] + 1
    L = len(riskmodel.lti)
    R = riskinput.hazard_getter.num_rlzs
    param['lrs_dt'] = numpy.dtype([('rlzi', U16), ('ratios', (F32, (L * I,)))])
    ass = []
    lrs_idx = AccumDict(accum=[])  # aid -> indices
    agg = numpy.zeros((E, R, L * I), F32)
    avg = AccumDict(accum={} if riskinput.by_site or not param['avg_losses']
                    else numpy.zeros(A, F64))
    result = dict(assratios=ass, lrs_idx=lrs_idx,
                  aids=riskinput.aids, avglosses=avg)
    if 'builder' in param:
        builder = param['builder']
        A = len(riskinput.aids)
        R = len(builder.weights)
        P = len(builder.return_periods)
        all_curves = numpy.zeros((A, R, P), builder.loss_dt)
        aid2idx = {aid: idx for idx, aid in enumerate(riskinput.aids)}
    # update the result dictionary and the agg array with each output
    for out in riskmodel.gen_outputs(riskinput, monitor):
        if len(out.eids) == 0:  # this happens for sites with no events
            continue
        r = out.rlzi
        eid2idx = riskinput.hazard_getter.eid2idx
        for l, loss_ratios in enumerate(out):
            if loss_ratios is None:  # for GMFs below the minimum_intensity
                continue
            loss_type = riskmodel.loss_types[l]
            indices = numpy.array([eid2idx[eid] for eid in out.eids])
            for a, asset in enumerate(out.assets):
                ratios = loss_ratios[a]  # shape (E, I)
                aid = asset.ordinal
                aval = asset.value(loss_type)
                losses = aval * ratios
                if 'builder' in param:
                    idx = aid2idx[aid]
                    for i in range(I):
                        lt = loss_type + '_ins' * i
                        all_curves[idx, r][lt] = builder.build_curve(
                            aval, ratios[:, i], r)

                # average losses
                if param['avg_losses']:
                    rat = ratios.sum(axis=0) * param['ses_ratio']
                    for i in range(I):
                        lba = avg[l + L * i, r]
                        try:
                            lba[aid] += rat[i]
                        except KeyError:
                            lba[aid] = rat[i]

                # agglosses, asset_loss_table
                for i in range(I):
                    li = l + L * i
                    # this is the critical loop: it is important to keep it
                    # vectorized in terms of the event indices
                    agg[indices, r, li] += losses[:, i]
                    if param['asset_loss_table']:
                        for eid, ratio in zip(out.eids, ratios[:, i]):
                            if ratio > 0:
                                ass.append((aid, r, eid, li, ratio))

    # collect agglosses
    idx = agg.nonzero()  # return only the nonzero values
    result['agglosses'] = (idx, agg[idx])
    # when there are asset loss ratios, group them in a composite array
    # of dtype lrs_dt, i.e. (rlzi, ratios)
    if param['asset_loss_table']:
        data = sorted(ass)  # sort by aid, r
        result['num_losses'] = num_losses = collections.Counter()  # by aid, r
        n = 0
        all_ratios = []
        for aid, agroup in itertools.groupby(data, operator.itemgetter(0)):
            for r, rgroup in itertools.groupby(agroup, operator.itemgetter(1)):
                for e, egroup in itertools.groupby(
                        rgroup, operator.itemgetter(2)):
                    ratios = numpy.zeros(L * I, F32)
                    for rec in egroup:
                        ratios[rec[3]] = rec[4]
                    all_ratios.append((r, ratios))
                    num_losses[aid, r] += 1
            n1 = len(all_ratios)
            lrs_idx[aid].append((n, n1))
            n = n1
        result['assratios'] = numpy.array(all_ratios, param['lrs_dt'])
        if 'builder' in param:
            result['curves_stats'] = builder.pair(
                all_curves, param['stats'])[1]
            if param['conditional_loss_poes']:
                loss_maps, result['loss_maps_stats'] = builder.build_maps(
                    all_curves, param['conditional_loss_poes'], param['stats'])

    # store info about the GMFs, must be done at the end
    result['gmdata'] = riskinput.gmdata
    return result


@base.calculators.add('event_based_risk')
class EbrCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the total losses by taxonomy
    """
    core_task = event_based_risk
    pre_calculator = 'event_based'
    is_stochastic = True

    def pre_execute(self):
        oq = self.oqparam
        if 'gmfs' in oq.inputs:
            assert not oq.hazard_calculation_id, (
                'You cannot use --hc together with gmfs_file')
            self.pre_calculator = None
            super().pre_execute()
            parent = ()
        elif oq.hazard_calculation_id:
            super().pre_execute()
            parent = self.datastore.parent
            oqp = parent['oqparam']
            if oqp.investigation_time != oq.investigation_time:
                raise ValueError(
                    'The parent calculation was using investigation_time=%s'
                    ' != %s' % (oqp.investigation_time, oq.investigation_time))
            if oqp.minimum_intensity != oq.minimum_intensity:
                raise ValueError(
                    'The parent calculation was using minimum_intensity=%s'
                    ' != %s' % (oqp.minimum_intensity, oq.minimum_intensity))
        else:
            ebcalc = base.calculators[self.pre_calculator](self.oqparam)
            ebcalc.run(close=False)
            self.set_log_format()
            parent = self.dynamic_parent = self.datastore.parent = (
                ebcalc.datastore)
            oq.hazard_calculation_id = parent.calc_id
            self.datastore['oqparam'] = oq
            self.param = ebcalc.param
            self.sitecol = ebcalc.sitecol
            self.assetcol = ebcalc.datastore['assetcol']
            self.riskmodel = ebcalc.riskmodel

        self.L = len(self.riskmodel.lti)
        self.T = len(self.assetcol.tagcol)
        self.A = len(self.assetcol)
        self.I = oq.insured_losses + 1
        if parent:
            self.datastore['csm_info'] = parent['csm_info']
            self.rlzs_assoc = parent['csm_info'].get_rlzs_assoc()
            self.param['builder'] = get_loss_builder(parent, oq.loss_dt())

        # sorting the eids is essential to get the epsilons in the right
        # order (i.e. consistent with the one used in ebr from ruptures)
        self.eids = (sorted(parent['events']['eid']) if parent
                     else sorted(self.datastore['events']['eid']))
        self.E = len(self.eids)
        eps = self.epsilon_getter()()
        self.riskinputs = self.build_riskinputs('gmf', eps, self.E)
        self.param['insured_losses'] = oq.insured_losses
        self.param['avg_losses'] = oq.avg_losses
        self.param['ses_ratio'] = oq.ses_ratio
        self.param['asset_loss_table'] = oq.asset_loss_table
        self.param['stats'] = oq.risk_stats()
        self.param['conditional_loss_poes'] = oq.conditional_loss_poes
        self.taskno = 0
        self.start = 0
        avg_losses = self.oqparam.avg_losses
        if avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, self.R, self.L * self.I))
        self.agglosses = numpy.zeros((self.E, self.R, self.L * self.I), F32)
        self.num_losses = numpy.zeros((self.A, self.R), U32)
        if oq.asset_loss_table:
            # save all_loss_ratios
            self.alr_nbytes = 0
            self.indices = collections.defaultdict(list)  # sid -> pairs

    def epsilon_getter(self):
        """
        :returns: a callable (start, stop) producing a slice of epsilons
        """
        return riskinput.make_epsilon_getter(
            len(self.assetcol), self.E,
            self.oqparam.asset_correlation,
            self.oqparam.master_seed,
            self.oqparam.ignore_covs or not self.riskmodel.covs)

    def save_losses(self, dic, offset=0):
        """
        Save the event loss tables incrementally.

        :param dic:
            dictionary with agglosses, assratios, avglosses, lrs_idx
        :param offset:
            realization offset
        """
        aids = dic.pop('aids')
        agglosses = dic.pop('agglosses')
        assratios = dic.pop('assratios')
        avglosses = dic.pop('avglosses')
        lrs_idx = dic.pop('lrs_idx')
        with self.monitor('saving event loss table', autoflush=True):
            idx, agg = agglosses
            self.agglosses[idx] += agg
        '''
        if self.oqparam.asset_loss_table:
            with self.monitor('saving loss ratios', autoflush=True):
                for (a, r), num in dic.pop('num_losses').items():
                    self.num_losses[a, r + offset] += num
                for aid, pairs in lrs_idx.items():
                    self.indices[aid].extend(
                        (start + self.start, stop + self.start)
                        for start, stop in pairs)
                self.start += len(assratios)
                assratios['rlzi'] += offset
                self.datastore.extend('all_loss_ratios/data', assratios)
                self.alr_nbytes += assratios.nbytes
        '''

        if not hasattr(self, 'vals'):
            self.vals = self.assetcol.values()
        with self.monitor('saving avg_losses-rlzs'):
            for (li, r), ratios in avglosses.items():
                l = li if li < self.L else li - self.L
                vs = self.vals[self.riskmodel.loss_types[l]]
                self.dset[aids, r, li] += numpy.array(
                    [ratios.get(aid, 0) * vs[aid] for aid in aids])

        if 'curves-stats' in dic:
            array = dic['curves-stats']  # shape (A, S, P)
            self.datastore['curves-stats'][aids] = array
        if 'loss_maps-stats' in dic:
            array = dic['loss_maps-stats']  # shape (A, R, P, LI)
            loss_maps = numpy.zeros(array.shape[:2], self.loss_maps_dt)
            for lti, lt in enumerate(self.loss_maps_dt.names):
                loss_maps[lt] = array[:, :, :, lti]
            self.datastore['loss_maps-stats'][aids] = loss_maps

        self.taskno += 1

    def combine(self, dummy, res):
        """
        :param dummy: unused parameter
        :param res: a result dictionary
        """
        self.save_losses(res, offset=0)
        return 1

    def post_execute(self, result):
        """
        Save risk data and possibly execute the EbrPostCalculator
        """
        oq = self.oqparam
        logging.info('Saving event loss table')
        elt_dt = numpy.dtype(
            [('eid', U64), ('rlzi', U16), ('loss', (F32, (self.L * self.I,)))])
        with self.monitor('saving event loss table', measuremem=True):
            # saving zeros is a lot faster than adding an `if loss.sum()`
            agglosses = numpy.fromiter(
                ((e, r, loss)
                 for e, losses in zip(self.eids, self.agglosses)
                 for r, loss in enumerate(losses) if loss.sum()), elt_dt)
            self.datastore['losses_by_event'] = agglosses
        self.postproc()

    def postproc(self):
        """
        Build aggregate loss curves and run EbrPostCalculator
        """
        dstore = self.datastore
        self.before_export()  # set 'realizations'
        oq = self.oqparam
        eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
        if eff_time < 2:
            logging.warn('eff_time=%s is too small to compute agg_curves',
                         eff_time)
            return
        stats = oq. risk_stats()
        # store avg_losses-stats
        if oq.avg_losses:
            set_rlzs_stats(self.datastore, 'avg_losses')
        b = get_loss_builder(dstore)
        if 'ruptures' in dstore:
            logging.info('Building loss tables')
            with self.monitor('building loss tables', measuremem=True):
                rlt, lbr = build_loss_tables(dstore)
                dstore['rup_loss_table'] = rlt
                dstore['losses_by_rlzi'] = lbr
                ridx = [rlt[:, lti].argmax() for lti in range(self.L)]
                dstore.set_attrs('rup_loss_table', ridx=ridx)
        logging.info('Building aggregate loss curves')
        with self.monitor('building agg_curves', measuremem=True):
            array, arr_stats = b.build(dstore['losses_by_event'].value, stats)
        self.datastore['agg_curves-rlzs'] = array
        units = self.assetcol.units(loss_types=array.dtype.names)
        self.datastore.set_attrs(
            'agg_curves-rlzs', return_periods=b.return_periods, units=units)
        if arr_stats is not None:
            self.datastore['agg_curves-stats'] = arr_stats
            self.datastore.set_attrs(
                'agg_curves-stats', return_periods=b.return_periods,
                stats=[encode(name) for (name, func) in stats], units=units)

        if 'all_loss_ratios' in self.datastore:
            self.datastore.save_vlen(
                'all_loss_ratios/indices',
                [numpy.array(self.indices[aid], riskinput.indices_dt)
                 for aid in range(self.A)])
            self.datastore.set_attrs(
                'all_loss_ratios',
                loss_types=' '.join(self.riskmodel.loss_types))
            dset = self.datastore['all_loss_ratios/data']
            nbytes = dset.size * dset.dtype.itemsize
            self.datastore.set_attrs(
                'all_loss_ratios/data',
                nbytes=nbytes, bytes_per_asset=nbytes / self.A)
            EbrPostCalculator(self).run(close=False)


# ######################### EbrPostCalculator ############################## #

def build_curves_maps(avalues, builder, lrgetter, stats, clp, monitor):
    """
    Build loss curves and optionally maps if conditional_loss_poes are set.
    """
    with monitor('getting loss ratios'):
        loss_ratios = lrgetter.get_all()
    curves, curves_stats = builder.build_all(avalues, loss_ratios, stats)
    loss_maps, loss_maps_stats = builder.build_maps(curves, clp, stats)
    res = {'aids': lrgetter.aids, 'loss_maps-rlzs': loss_maps}
    if loss_maps_stats is not None:
        res['loss_maps-stats'] = loss_maps_stats
    if curves_stats is not None:
        res['curves-stats'] = curves_stats
    return res


class EbrPostCalculator(base.RiskCalculator):
    def __init__(self, calc):
        self.datastore = calc.datastore
        self.oqparam = calc.oqparam
        self._monitor = calc._monitor
        self.riskmodel = calc.riskmodel
        self.loss_builder = get_loss_builder(calc.datastore)
        P = len(self.oqparam.conditional_loss_poes)
        self.loss_maps_dt = self.oqparam.loss_dt((F32, (P,)))

    def save_curves_maps(self, acc, res):
        """
        Save the loss curves and maps (if any).

        :returns: the total number of stored bytes.
        """
        for key in res:
            if key == 'curves-stats':
                array = res[key]  # shape (A, S, P)
                self.datastore[key][res['aids']] = array
            elif key.startswith('loss_maps'):
                array = res[key]  # shape (A, R, P, LI)
                loss_maps = numpy.zeros(array.shape[:2], self.loss_maps_dt)
                for lti, lt in enumerate(self.loss_maps_dt.names):
                    loss_maps[lt] = array[:, :, :, lti]
                acc += {key: loss_maps.nbytes}
                self.datastore[key][res['aids']] = loss_maps
                self.datastore.set_attrs(key, nbytes=acc[key])
        return acc

    def pre_execute(self):
        pass

    def execute(self):
        oq = self.oqparam
        R = len(self.loss_builder.weights)
        # build loss maps
        if 'all_loss_ratios' in self.datastore and oq.conditional_loss_poes:
            assetcol = self.datastore['assetcol']
            stats = oq.risk_stats()
            builder = self.loss_builder
            A = len(assetcol)
            S = len(stats)
            P = len(builder.return_periods)
            # create loss_maps datasets
            self.datastore.create_dset(
                'loss_maps-rlzs', self.loss_maps_dt, (A, R), fillvalue=None)
            if R > 1:
                self.datastore.create_dset(
                    'loss_maps-stats', self.loss_maps_dt, (A, S),
                    fillvalue=None)
                self.datastore.set_attrs(
                    'loss_maps-stats',
                    stats=[encode(name) for (name, func) in stats])
                self.datastore.create_dset(
                    'curves-stats', oq.loss_dt(), (A, S, P), fillvalue=None)
                self.datastore.set_attrs(
                    'curves-stats', return_periods=builder.return_periods,
                    stats=[encode(name) for (name, func) in stats])
            mon = self.monitor('loss maps')
            lazy = ('all_loss_ratios' in self.datastore.parent
                    and self.can_read_parent())
            logging.info('Instantiating LossRatiosGetters')
            with self.monitor('building lrgetters', measuremem=True,
                              autoflush=True):
                allargs = []
                for aids in split_in_blocks(range(A), oq.concurrent_tasks):
                    dstore = self.datastore.parent if lazy else self.datastore
                    getter = getters.LossRatiosGetter(dstore, aids, lazy)
                    # a lazy getter will read the loss_ratios from the workers
                    # an eager getter reads the loss_ratios upfront
                    allargs.append((assetcol.values(aids), builder, getter,
                                    stats, oq.conditional_loss_poes, mon))
            if lazy:
                # avoid OSError: Can't read data (Wrong b-tree signature)
                self.datastore.parent.close()
            parallel.Starmap(build_curves_maps, allargs).reduce(
                self.save_curves_maps)
            if lazy:  # the parent was closed, reopen it
                self.datastore.parent.open()

    def post_execute(self):
        # override the base class method to avoid doing bad stuff
        pass
