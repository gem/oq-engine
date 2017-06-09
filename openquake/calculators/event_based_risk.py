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

from openquake.baselib.python3compat import zip
from openquake.baselib.general import AccumDict, block_splitter
from openquake.hazardlib.stats import compute_stats
from openquake.commonlib import util
from openquake.calculators import base, event_based
from openquake.baselib import parallel
from openquake.risklib import riskinput, scientific
from openquake.baselib.parallel import Starmap

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64
getweight = operator.attrgetter('weight')


def build_agg_curve(cb_inputs, monitor):
    """
    Build the aggregate loss curve in parallel for each loss type
    and realization pair.

    :param cb_inputs:
        a list of triples `(cbs, rlzname, data)` where `cbs` are the curve
        builders, `rlzname` is a string of kind `rlz-%03d` and `data` is an
        array of kind `(eid, loss)`
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary (r, l, i) -> (losses, poes, avg)
    """
    result = {}
    for cbs, rlzname, data in cb_inputs:
        if len(data) == 0:  # realization with no losses
            continue
        r = int(rlzname[4:])  # strip rlz-
        for cb in cbs:
            l = cb.index
            losses = data['loss'][:, l]  # shape (E, I)
            for i in range(cb.insured_losses + 1):
                result[l, r, i] = cb.calc_agg_curve(losses[:, i])
    return result


def _aggregate(outputs, compositemodel, taxid, agg, idx, result, param):
    # update the result dictionary and the agg array with each output
    L = len(compositemodel.lti)
    I = param['insured_losses'] + 1
    losses_by_taxon = result['losses_by_taxon']
    ass = result['assratios']
    for outs in outputs:
        r = outs.r
        aggr = agg[r]  # array of zeros of shape (E, L, I)
        for l, out in enumerate(outs):
            if out is None:  # for GMFs below the minimum_intensity
                continue
            loss_ratios, eids = out
            loss_type = compositemodel.loss_types[l]
            indices = numpy.array([idx[eid] for eid in eids])
            for aid, asset in enumerate(outs.assets):
                ratios = loss_ratios[aid]
                aid = asset.ordinal
                losses = ratios * asset.value(loss_type)  # shape (E, I)

                # average losses
                if param['avg_losses']:
                    rat = ratios.sum(axis=0) * param['ses_ratio']
                    for i in range(I):
                        result['avglosses'][l + L * i, r][aid] += rat[i]

                # agglosses
                aggr[indices, l] += losses

                # losses by taxonomy
                t = taxid[asset.taxonomy]
                for i in range(I):
                    losses_by_taxon[t, r, l + L * i] += losses[:, i].sum()

                if param['asset_loss_table']:
                    for i in range(I):
                        li = l + L * i
                        for eid, ratio in zip(eids, ratios[:, i]):
                            if ratio > 0:
                                ass.append((aid, r, eid, li, ratio))

    # when there are asset loss ratios, group them in a composite array
    # of dtype lrs_dt, i.e. (rlzi, ratios)
    data = sorted(ass)  # sort by aid, r
    lrs_idx = result['lrs_idx']  # shape (A, 2)
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
        n1 = len(all_ratios)
        lrs_idx[aid] = [n, n1]
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
    A = len(assetcol)
    I = param['insured_losses'] + 1
    eids = riskinput.hazard_getter.eids
    E = len(eids)
    L = len(riskmodel.lti)
    taxid = {t: i for i, t in enumerate(sorted(assetcol.taxonomies))}
    T = len(taxid)
    R = sum(len(rlzs)
            for gsim, rlzs in riskinput.hazard_getter.rlzs_by_gsim.items())
    param['lrs_dt'] = numpy.dtype([('rlzi', U16), ('ratios', (F32, (L * I,)))])
    idx = dict(zip(eids, range(E)))
    agg = AccumDict(accum=numpy.zeros((E, L, I), F32))  # r -> array
    result = dict(agglosses=AccumDict(), assratios=[],
                  lrs_idx=numpy.zeros((A, 2), U32),
                  losses_by_taxon=numpy.zeros((T, R, L * I), F32),
                  aids=None)
    if param['avg_losses']:
        result['avglosses'] = AccumDict(accum=numpy.zeros(A, F64))
    else:
        result['avglosses'] = {}
    outputs = riskmodel.gen_outputs(riskinput, monitor, assetcol)
    _aggregate(outputs, riskmodel, taxid, agg, idx, result, param)
    for r in sorted(agg):
        records = [(eids[i], loss) for i, loss in enumerate(agg[r])
                   if loss.sum() > 0]
        if records:
            result['agglosses'][r] = numpy.array(records, param['elt_dt'])

    # store info about the GMFs
    result['gmdata'] = riskinput.gmdata
    return result


@util.reader
def build_loss_maps(assets, builder, getter, rlzs, stats, monitor):
    """
    Thin wrapper over :meth:
    `openquake.risklib.scientific.CurveBuilder.build_maps`.
    :returns: assets IDs and loss maps for the given chunk of assets
    """
    getter.dstore.open()  # if not already open
    aids, loss_maps, loss_maps_stats = builder.build_maps(
        assets, getter, rlzs, stats, monitor)
    res = {'aids': aids, 'loss_maps-rlzs': loss_maps}
    if loss_maps_stats is not None:
        res['loss_maps-stats'] = loss_maps_stats
    return res


class EbrPostCalculator(base.RiskCalculator):
    def __init__(self, calc):
        self.datastore = calc.datastore
        self.oqparam = calc.oqparam
        self._monitor = calc._monitor
        self.riskmodel = calc.riskmodel
        self.rlzs_assoc = calc.rlzs_assoc

    def cb_inputs(self, table):
        loss_table = self.datastore[table]
        cb = self.riskmodel.curve_builder
        return [(cb, rlzstr, loss_table[rlzstr].value)
                for rlzstr in loss_table]

    def save_loss_maps(self, acc, res):
        """
        Save the loss maps by opening and closing the datastore and
        return the total number of stored bytes.
        """
        for key in res:
            if key.startswith('loss_maps'):
                acc += {key: res[key].nbytes}
                self.datastore[key][res['aids']] = res[key]
                self.datastore.set_attrs(key, nbytes=acc[key])
        return acc

    def pre_execute(self):
        pass

    def execute(self):
        # build loss maps
        if ('all_loss_ratios' in self.datastore
                 and self.oqparam.conditional_loss_poes):
            assetcol = self.assetcol
            rlzs = self.rlzs_assoc.realizations
            stats = self.oqparam.risk_stats()
            builder = self.riskmodel.curve_builder
            A = len(assetcol)
            R = len(self.datastore['realizations'])
            # create loss_maps datasets
            self.datastore.create_dset(
                'loss_maps-rlzs', builder.loss_maps_dt, (A, R), fillvalue=None)
            if R > 1:
                self.datastore.create_dset(
                    'loss_maps-stats', builder.loss_maps_dt, (A, len(stats)),
                    fillvalue=None)
            mon = self.monitor('loss maps')
            if self.oqparam.hazard_calculation_id and (
                    'asset_loss_table' in self.datastore.parent):
                Starmap = parallel.Starmap  # we can parallelize fully
                lrgetter = riskinput.LossRatiosGetter(self.datastore.parent)
                # avoid OSError: Can't read data (Wrong b-tree signature)
                self.datastore.parent.close()
            else:  # there is a single datastore
                # we cannot read from it in parallel while writing
                Starmap = parallel.Sequential
                lrgetter = riskinput.LossRatiosGetter(self.datastore)
            Starmap.apply(
                build_loss_maps,
                (assetcol, builder, lrgetter, rlzs, stats, mon),
                self.oqparam.concurrent_tasks
            ).reduce(self.save_loss_maps)
            if self.oqparam.hazard_calculation_id:
                self.datastore.parent.open()

        # build an aggregate loss curve per realization
        if 'agg_loss_table' in self.datastore:
            self.build_agg_curve()

    def post_execute(self):
        # override the base class method to avoid doing bad stuff
        pass

    def build_agg_curve(self):
        """
        Build a single loss curve per realization. It is NOT obtained
        by aggregating the loss curves; instead, it is obtained without
        generating the loss curves, directly from the the aggregate losses.
        """
        oq = self.oqparam
        cr = {cb.loss_type: cb.curve_resolution
              for cb in self.riskmodel.curve_builder}
        loss_curve_dt, _ = scientific.build_loss_dtypes(
            cr, oq.conditional_loss_poes)
        lts = self.riskmodel.loss_types
        cb_inputs = self.cb_inputs('agg_loss_table')
        I = oq.insured_losses + 1
        R = len(self.rlzs_assoc.realizations)
        # NB: using the Processmap since celery is hanging; the computation
        # is fast anyway and this part will likely be removed in the future
        result = parallel.Processmap.apply(
            build_agg_curve, (cb_inputs, self.monitor('')),
            concurrent_tasks=self.oqparam.concurrent_tasks).reduce()
        agg_curve = numpy.zeros((I, R), loss_curve_dt)
        for l, r, i in result:
            agg_curve[lts[l]][i, r] = result[l, r, i]
        self.datastore['agg_curve-rlzs'] = agg_curve

        if R > 1:  # save stats too
            statnames, stats = zip(*oq.risk_stats())
            weights = self.datastore['realizations']['weight']
            agg_curve_stats = numpy.zeros((I, len(stats)), agg_curve.dtype)
            for l, loss_type in enumerate(agg_curve.dtype.names):
                acs = agg_curve_stats[loss_type]
                data = agg_curve[loss_type]
                for i in range(I):
                    avg = data['avg'][i]
                    losses, all_poes = scientific.normalize_curves_eb(
                        [(c['losses'], c['poes']) for c in data[i]])
                    acs['losses'][i] = losses
                    acs['poes'][i] = compute_stats(all_poes, stats, weights)
                    acs['avg'][i] = compute_stats(avg, stats, weights)

            self.datastore['agg_curve-stats'] = agg_curve_stats


elt_dt = numpy.dtype([('eid', U64), ('loss', F32)])

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
                    assetcol, riskmodel, imts, trunc_level, correl_model,
                    min_iml, monitor):
        """
        :param sm_id: source model ordinal
        :param ruptures_by_grp: dictionary of ruptures by src_group_id
        :param sitecol: a SiteCollection instance
        :param assetcol: an AssetCollection instance
        :param riskmodel: a RiskModel instance
        :param imts: a list of Intensity Measure Types
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
        for grp_id in grp_ids:
            rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(grp_id)
            samples = rlzs_assoc.samples[grp_id]
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
                    grp_id, rlzs_by_gsim, rupts, sitecol, imts, min_iml,
                    trunc_level, correl_model, samples)
                ri = riskinput.RiskInputFromRuptures(getter, eps)
                allargs.append((ri, riskmodel, assetcol, monitor))

        self.vals = self.assetcol.values()
        taskname = '%s#%d' % (event_based_risk.__name__, sm_id + 1)
        ires = Starmap(event_based_risk, allargs, name=taskname).submit_all()
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
        imts = list(oq.imtls)
        elt_dt = numpy.dtype([('eid', U64), ('loss', (F32, (self.L, self.I)))])
        csm_info = self.datastore['csm_info']
        mon = self.monitor('risk')
        for sm in csm_info.source_models:
            param = dict(
                assetcol=self.assetcol,
                ses_ratio=oq.ses_ratio,
                loss_dt=oq.loss_dt(), elt_dt=elt_dt,
                asset_loss_table=bool(oq.asset_loss_table or oq.loss_ratios),
                avg_losses=oq.avg_losses,
                insured_losses=oq.insured_losses,
                ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
                maximum_distance=oq.maximum_distance,
                samples=sm.samples,
                seed=self.oqparam.random_seed)
            yield (sm.ordinal, ruptures_by_grp, self.sitecol.complete,
                   param, self.riskmodel, imts, oq.truncation_level,
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
        self.R = num_rlzs
        self.A = len(self.assetcol)
        num_tax = len(self.assetcol.taxonomies)
        self.datastore.create_dset('losses_by_taxon-rlzs', F32,
                                   (num_tax, self.R, self.L * self.I))

        if self.oqparam.asset_loss_table or self.oqparam.loss_ratios:
            # save all_loss_ratios
            self.T = sum(ires.num_tasks for ires in allres)
            self.alr_nbytes = 0
            self.datastore.create_dset(
                'all_loss_ratios/indices', U32, (self.A, self.T, 2))

        avg_losses = self.oqparam.avg_losses
        if avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, self.R, self.L * self.I))

        num_events = collections.Counter()
        self.gmdata = {}
        self.taskno = 0
        self.start = 0
        for res in allres:
            start, stop = res.rlz_slice.start, res.rlz_slice.stop
            for dic in res:
                self.gmdata += dic.pop('gmdata')
                self.save_losses(dic, start)
            logging.debug(
                'Saving results for source model #%d, realizations %d:%d',
                res.sm_id + 1, start, stop)
            if hasattr(res, 'ruptures_by_grp'):
                save_ruptures(self, res.ruptures_by_grp)
            elif hasattr(res, 'events_by_grp'):
                for grp_id in res.events_by_grp:
                    events = res.events_by_grp[grp_id]
                    self.datastore.extend('events/grp-%02d' % grp_id, events)
            num_events[res.sm_id] += res.num_events
        event_based.save_gmdata(self, num_rlzs)
        return num_events

    def save_losses(self, dic, offset=0):
        """
        Save the event loss tables incrementally.

        :param dic:
            dictionary with agglosses, assratios, losses_by_taxon, avglosses,
            lrs_idx
        :param offset:
            realization offset
        """
        aids = dic.pop('aids')
        agglosses = dic.pop('agglosses')
        assratios = dic.pop('assratios')
        losses_by_taxon = dic.pop('losses_by_taxon')
        avglosses = dic.pop('avglosses')
        lrs_idx = dic.pop('lrs_idx')
        with self.monitor('saving event loss table', autoflush=True):
            for r in agglosses:
                key = 'agg_loss_table/rlz-%03d' % (r + offset)
                self.datastore.extend(key, agglosses[r])

        if self.oqparam.asset_loss_table or self.oqparam.loss_ratios:
            with self.monitor('saving loss ratios', autoflush=True):
                lrs_idx += self.start
                self.start += len(assratios)
                self.datastore['all_loss_ratios/indices'][
                    :, self.taskno] = lrs_idx
                assratios['rlzi'] += offset
                self.datastore.extend('all_loss_ratios/data', assratios)
                self.alr_nbytes += assratios.nbytes

        # saving losses by taxonomy is ultra-fast, so it is not monitored
        dset = self.datastore['losses_by_taxon-rlzs']
        for r in range(losses_by_taxon.shape[1]):
            if aids is None:
                dset[:, r + offset, :] += losses_by_taxon[:, r, :]
            else:
                dset[aids, r + offset, :] += losses_by_taxon[:, r, :]

        with self.monitor('saving avg_losses-rlzs'):
            for (li, r), ratios in avglosses.items():
                l = li if li < self.L else li - self.L
                vs = self.vals[self.riskmodel.loss_types[l]]
                if aids is None:
                    self.dset[:, r + offset, li] += ratios * vs
                else:
                    self.dset[aids, r + offset, li] += ratios * vs
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
            for rlzname in self.datastore['agg_loss_table']:
                self.datastore.set_nbytes('agg_loss_table/' + rlzname)
            self.datastore.set_nbytes('agg_loss_table')
            E = sum(num_events.values())
            agglt = self.datastore['agg_loss_table']
            for rlz, dset in agglt.items():
                dset.attrs['nonzero_fraction'] = len(dset) / E

        if 'all_loss_ratios' in self.datastore:
            self.datastore.set_attrs(
                'all_loss_ratios',
                loss_types=' '.join(self.riskmodel.loss_types))
            for name in ('indices', 'data'):
                dset = self.datastore['all_loss_ratios/' + name]
                nbytes = dset.size * dset.dtype.itemsize
                self.datastore.set_attrs(
                    'all_loss_ratios/' + name,
                    nbytes=nbytes, bytes_per_asset=nbytes / self.A)
            EbrPostCalculator(self).run(close=False)
