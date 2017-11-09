# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

from openquake.baselib.python3compat import zip, encode
from openquake.baselib.general import (
    AccumDict, block_splitter, split_in_blocks, group_array)
from openquake.baselib import config
from openquake.calculators import base, event_based
from openquake.calculators.export.loss_curves import get_loss_builder
from openquake.baselib import parallel
from openquake.risklib import riskinput

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64
getweight = operator.attrgetter('weight')
indices_dt = numpy.dtype([('start', U32), ('stop', U32)])


def _aggregate(outputs, compositemodel, agg, all_eids, result, param):
    # update the result dictionary and the agg array with each output
    E = len(all_eids)
    L = len(compositemodel.lti)
    I = param['insured_losses'] + 1
    ass = result['assratios']
    idx = dict(zip(all_eids, range(E)))
    aids = result['aids']
    for out in outputs:
        r = out.rlzi
        for l, loss_ratios in enumerate(out):
            if loss_ratios is None:  # for GMFs below the minimum_intensity
                continue
            loss_type = compositemodel.loss_types[l]
            indices = numpy.array([idx[eid] for eid in out.eids])

            for a, asset in enumerate(out.assets):
                ratios = loss_ratios[a]  # shape (E, I)
                aid = asset.ordinal
                losses = ratios * asset.value(loss_type)

                # average losses
                if param['avg_losses']:
                    rat = ratios.sum(axis=0) * param['ses_ratio']
                    ai = aid if aids is None else a
                    for i in range(I):
                        result['avglosses'][l + L * i, r][ai] += rat[i]

                # agglosses
                for i in range(I):
                    # this is the critical loop: it is import to keep it
                    # vectorized in terms of the event indices
                    agg[indices, r, l + L * i] += losses[:, i]

                if param['asset_loss_table']:
                    for i in range(I):
                        li = l + L * i
                        for eid, ratio in zip(out.eids, ratios[:, i]):
                            if ratio > 0:
                                ass.append((aid, r, eid, li, ratio))

    # store agglosses
    it = ((eid, r, losses)
          for eid, all_losses in zip(all_eids, agg)
          for r, losses in enumerate(all_losses) if losses.sum())
    result['agglosses'] = numpy.fromiter(it, param['elt_dt'])

    # when there are asset loss ratios, group them in a composite array
    # of dtype lrs_dt, i.e. (rlzi, ratios)
    if param['asset_loss_table']:
        data = sorted(ass)  # sort by aid, r
        lrs_idx = result['lrs_idx']  # aid -> indices
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
    riskinput.hazard_getter.init()
    assetcol = param['assetcol']
    eids = riskinput.hazard_getter.eids
    E = len(eids)
    I = param['insured_losses'] + 1
    L = len(riskmodel.lti)
    aids = getattr(riskinput, 'aids', None)
    A = len(assetcol) if aids is None else len(aids)
    R = riskinput.hazard_getter.num_rlzs
    param['lrs_dt'] = numpy.dtype([('rlzi', U16), ('ratios', (F32, (L * I,)))])
    agg = numpy.zeros((E, R, L * I), F32)
    result = dict(assratios=[], lrs_idx=AccumDict(accum=[]), aids=aids)
    if param['avg_losses']:
        # dict (l, r) -> A losses
        result['avglosses'] = AccumDict(accum=numpy.zeros(A, F64))
    else:
        result['avglosses'] = {}
    outputs = riskmodel.gen_outputs(riskinput, monitor, assetcol)
    _aggregate(outputs, riskmodel, agg, eids, result, param)

    # store info about the GMFs
    result['gmdata'] = riskinput.gmdata
    return result

save_ruptures = event_based.EventBasedRuptureCalculator.__dict__[
    'save_ruptures']


class EpsilonMatrix0(object):
    """
    Mock-up for a matrix of epsilons of size N x E,
    used when asset_correlation=0.

    :param num_assets: N assets
    :param seeds: E seeds, set before calling numpy.random.normal
    """
    def __init__(self, num_assets, seeds):
        self.num_assets = num_assets
        self.seeds = seeds
        self.eps = None

    def make_eps(self):
        """
        Builds a matrix of N x E epsilons
        """
        eps = numpy.zeros((self.num_assets, len(self.seeds)), F32)
        for i, seed in enumerate(self.seeds):
            numpy.random.seed(seed)
            eps[:, i] = numpy.random.normal(size=self.num_assets)
        return eps

    def __getitem__(self, item):
        if self.eps is None:
            self.eps = self.make_eps()
        return self.eps[item]


class EpsilonMatrix1(object):
    """
    Mock-up for a matrix of epsilons of size N x E,
    used when asset_correlation=1.

    :param num_events: number of events
    :param seed: seed used to generate E epsilons
    """
    def __init__(self, num_events, seed):
        self.num_events = num_events
        self.seed = seed
        numpy.random.seed(seed)
        self.eps = numpy.random.normal(size=num_events)

    def __getitem__(self, item):
        # item[0] is the asset index, item[1] the event index
        # the epsilons are equal for all assets since asset_correlation=1
        return self.eps[item[1]]


@base.calculators.add('event_based_risk')
class EbriskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the total losses by taxonomy
    """
    pre_calculator = 'event_based_rupture'
    is_stochastic = True

    # TODO: if the number of source models is larger than concurrent_tasks
    # a different strategy should be used; the one used here is good when
    # there are few source models, so that we cannot parallelize on those
    def start_tasks(self, sm_id, ruptures_by_grp, sitecol,
                    assetcol, riskmodel, imtls, trunc_level, correl_model,
                    min_iml, monitor):
        """
        :param sm_id: source model ordinal
        :param ruptures_by_grp: dictionary of ruptures by src_group_id
        :param sitecol: a SiteCollection instance
        :param assetcol: an AssetCollection instance
        :param riskmodel: a RiskModel instance
        :param imtls: Intensity Measure Types and Levels
        :param trunc_level: truncation level
        :param correl_model: correlation model
        :param min_iml: vector of minimum intensities, one per IMT
        :param monitor: a Monitor instance
        :returns: an IterResult instance
        """
        csm_info = self.csm_info.get_info(sm_id)
        grp_ids = sorted(csm_info.get_sm_by_grp())
        rlzs_assoc = csm_info.get_rlzs_assoc()
        num_events = sum(ebr.multiplicity for grp in ruptures_by_grp
                         for ebr in ruptures_by_grp[grp])
        seeds = self.oqparam.random_seed + numpy.arange(num_events)

        allargs = []
        # prepare the risk inputs
        ruptures_per_block = self.oqparam.ruptures_per_block
        start = 0
        ignore_covs = self.oqparam.ignore_covs
        try:
            csm_info = self.csm.info
        except AttributeError:  # there is no .csm if --hc was given
            csm_info = self.datastore['csm_info']
        samples_by_grp = csm_info.get_samples_by_grp()
        for grp_id in grp_ids:
            rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(grp_id)
            samples = samples_by_grp[grp_id]
            for rupts in block_splitter(
                    ruptures_by_grp.get(grp_id, []), ruptures_per_block):
                if ignore_covs or not self.riskmodel.covs:
                    eps = None
                elif self.oqparam.asset_correlation:
                    eps = EpsilonMatrix1(num_events, self.oqparam.master_seed)
                else:
                    n_events = sum(ebr.multiplicity for ebr in rupts)
                    eps = EpsilonMatrix0(
                        len(self.assetcol), seeds[start: start + n_events])
                    start += n_events
                getter = riskinput.GmfGetter(
                    rlzs_by_gsim, rupts, sitecol, imtls, min_iml,
                    trunc_level, correl_model, samples)
                ri = riskinput.RiskInputFromRuptures(getter, eps)
                allargs.append((ri, riskmodel, assetcol, monitor))

        self.vals = self.assetcol.values()
        taskname = '%s#%d' % (event_based_risk.__name__, sm_id + 1)
        ires = parallel.Starmap(
            event_based_risk, allargs, name=taskname).submit_all()
        ires.num_ruptures = {
            sg_id: len(rupts) for sg_id, rupts in ruptures_by_grp.items()}
        ires.num_events = num_events
        ires.num_rlzs = len(rlzs_assoc.realizations)
        ires.sm_id = sm_id
        return ires

    def gen_args(self, ruptures_by_grp):
        """
        Yield the arguments required by build_ruptures, i.e. the
        source models, the asset collection, the riskmodel and others.
        """
        oq = self.oqparam
        self.L = len(self.riskmodel.lti)
        self.I = oq.insured_losses + 1
        correl_model = oq.get_correl_model()
        min_iml = self.get_min_iml(oq)
        imtls = oq.imtls
        elt_dt = numpy.dtype(
            [('eid', U64), ('rlzi', U16), ('loss', (F32, (self.L * self.I,)))])
        csm_info = self.datastore['csm_info']
        mon = self.monitor('risk')
        for sm in csm_info.source_models:
            param = dict(
                assetcol=self.assetcol,
                ses_ratio=oq.ses_ratio,
                loss_dt=oq.loss_dt(), elt_dt=elt_dt,
                asset_loss_table=oq.asset_loss_table,
                avg_losses=oq.avg_losses,
                insured_losses=oq.insured_losses,
                ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
                maximum_distance=oq.maximum_distance,
                samples=sm.samples,
                seed=self.oqparam.random_seed)
            yield (sm.ordinal, ruptures_by_grp, self.sitecol.complete,
                   param, self.riskmodel, imtls, oq.truncation_level,
                   correl_model, min_iml, mon)

    def execute(self):
        """
        Run the calculator and aggregate the results
        """
        if self.oqparam.number_of_logic_tree_samples:
            logging.warn('The event based risk calculator with sampling is '
                         'EXPERIMENTAL, UNTESTED and SLOW')
        if self.oqparam.ground_motion_fields:
            logging.warn('To store the ground motion fields change '
                         'calculation_mode = event_based')
        if self.oqparam.hazard_curves_from_gmfs:
            logging.warn('To compute the hazard curves change '
                         'calculation_mode = event_based')

        if 'all_loss_ratios' in self.datastore:
            EbrPostCalculator(self).run(close=False)
            return

        self.csm_info = self.datastore['csm_info']
        with self.monitor('reading ruptures', autoflush=True):
            ruptures_by_grp = (
                self.precalc.result if self.precalc
                else event_based.get_ruptures_by_grp(self.datastore.parent))
            # the ordering of the ruptures is essential for repeatibility
            for grp in ruptures_by_grp:
                ruptures_by_grp[grp].sort(key=operator.attrgetter('serial'))
        num_rlzs = 0
        allres = []
        source_models = self.csm_info.source_models
        self.sm_by_grp = self.csm_info.get_sm_by_grp()
        for i, args in enumerate(self.gen_args(ruptures_by_grp)):
            ires = self.start_tasks(*args)
            allres.append(ires)
            ires.rlz_slice = slice(num_rlzs, num_rlzs + ires.num_rlzs)
            num_rlzs += ires.num_rlzs
            for sg in source_models[i].src_groups:
                sg.eff_ruptures = ires.num_ruptures.get(sg.id, 0)
        num_events = self.save_results(allres, num_rlzs)
        return num_events  # {sm_id: #events}

    def save_results(self, allres, num_rlzs):
        """
        :param allres: an iterable of result iterators
        :param num_rlzs: the total number of realizations
        :returns: the total number of events
        """
        oq = self.oqparam
        self.R = num_rlzs
        self.A = len(self.assetcol)
        self.tagmask = self.assetcol.tagmask()  # shape (A, T)
        if oq.asset_loss_table:
            # save all_loss_ratios
            self.alr_nbytes = 0
            self.indices = collections.defaultdict(list)  # sid -> pairs

        if oq.avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, self.R, self.L * self.I))

        num_events = collections.Counter()
        self.gmdata = AccumDict(accum=numpy.zeros(len(oq.imtls) + 2, F32))
        self.taskno = 0
        self.start = 0
        self.num_losses = numpy.zeros((self.A, self.R), U32)
        for res in allres:
            start, stop = res.rlz_slice.start, res.rlz_slice.stop
            for dic in res:
                for r, arr in dic.pop('gmdata').items():
                    self.gmdata[start + r] += arr
                self.save_losses(dic, start)
            logging.debug(
                'Saving results for source model #%d, realizations %d:%d',
                res.sm_id + 1, start, stop)
            if hasattr(res, 'ruptures_by_grp'):  # for UCERF
                save_ruptures(self, res.ruptures_by_grp)
            elif hasattr(res, 'events_by_grp'):  # for UCERF
                for grp_id in res.events_by_grp:
                    events = res.events_by_grp[grp_id]
                    self.datastore.extend('events', events)
            num_events[res.sm_id] += res.num_events
        if 'all_loss_ratios' in self.datastore:
            self.datastore['all_loss_ratios/num_losses'] = self.num_losses
            self.datastore.set_attrs(
                'all_loss_ratios/num_losses', nbytes=self.num_losses.nbytes)
        del self.num_losses
        event_based.save_gmdata(self, num_rlzs)
        return num_events

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
            if self.oqparam.calculation_mode == 'gmf_ebrisk':
                for er, arr in group_array(agglosses, 'eid', 'rlzi').items():
                    self.agglosses[er] += arr['loss'].sum(axis=0)  # shape LI
            else:
                agglosses['rlzi'] += offset
                self.datastore.extend('agg_loss_table', agglosses)

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

        with self.monitor('saving avg_losses-rlzs'):
            for (li, r), ratios in avglosses.items():
                l = li if li < self.L else li - self.L
                if aids is None:  # event_based_risk
                    vs = self.vals[self.riskmodel.loss_types[l]]
                    self.dset[:, r + offset, li] += ratios * vs
                else:  # gmf_ebrisk, there is no offset
                    vs = self.vals[aids][self.riskmodel.loss_types[l]]
                    self.dset[aids, r, li] += ratios * vs
        self.taskno += 1

    def post_execute(self, num_events):
        """
        Save risk data and possibly execute the EbrPostCalculator
        """
        # gmv[:-2] are the total gmv per each IMT
        gmv = sum(gm[:-2].sum() for gm in self.gmdata.values())
        if not gmv:
            raise RuntimeError('No GMFs were generated, perhaps they were '
                               'all below the minimum_intensity threshold')

        if 'agg_loss_table' not in self.datastore:
            logging.warning(
                'No losses were generated: most likely there is an error in y'
                'our input files or the GMFs were below the minimum intensity')
        else:
            self.datastore.set_nbytes('agg_loss_table')
            E = sum(num_events.values())
            agglt = self.datastore['agg_loss_table']
            agglt.attrs['nonzero_fraction'] = len(agglt) / E

        # build aggregate loss curves
        self.before_export()  # set 'realizations'
        oq = self.oqparam
        b = get_loss_builder(self.datastore)
        alt = self.datastore['agg_loss_table']
        stats = oq.risk_stats()
        array, array_stats = b.build(alt, stats)
        self.datastore['agg_curves-rlzs'] = array
        units = self.assetcol.units(loss_types=array.dtype.names)
        self.datastore.set_attrs(
            'agg_curves-rlzs', return_periods=b.return_periods, units=units)
        if array_stats is not None:
            self.datastore['agg_curves-stats'] = array_stats
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
            assetcol = self.assetcol
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
            read_access = (bool(config.directory.shared_dir)
                           if config.distribution.oq_distribute == 'celery'
                           else True)
            lazy = (oq.hazard_calculation_id and 'all_loss_ratios'
                    in self.datastore.parent and read_access)
            logging.info('Instantiating LossRatiosGetters')
            with self.monitor('building lrgetters', measuremem=True,
                              autoflush=True):
                allargs = []
                for aids in split_in_blocks(range(A), oq.concurrent_tasks):
                    dstore = self.datastore.parent if lazy else self.datastore
                    getter = riskinput.LossRatiosGetter(dstore, aids, lazy)
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
