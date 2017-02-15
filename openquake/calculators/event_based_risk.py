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
import collections
import numpy

from openquake.baselib.python3compat import zip
from openquake.baselib.general import (
    AccumDict, humansize, block_splitter, group_array)
from openquake.hazardlib.stats import compute_stats, compute_stats2
from openquake.calculators import base, event_based
from openquake.baselib import parallel
from openquake.risklib import riskinput, scientific
from openquake.baselib.parallel import Starmap

U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
getweight = operator.attrgetter('weight')


def build_el_dtypes(loss_types, insured_losses):
    """
    :param loss_types:
        list of loss type strings
    :param bool insured_losses:
        job.ini configuration parameter
    :returns:
        ela_dt and elt_dt i.e. the data types for event loss assets and
        event loss table respectively
    """
    I = insured_losses + 1
    L = len(loss_types)
    ela_list = [('eid', U32), ('aid', U32), ('loss', (F32, (L, I)))]
    elt_list = [('eid', U32), ('loss', (F32, (L, I)))]
    return numpy.dtype(ela_list), numpy.dtype(elt_list)


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


def build_rcurves(cb_inputs, assets, monitor):
    """
    :param cb_inputs: triples `(cbs, rlzname, data)`
    :param assets: full list of assets
    :param monitor: Monitor instance
    """
    result = {}
    for cbs, rlzname, data in cb_inputs:
        losses_by_aid = group_array(data, 'aid')
        for cb in cbs:
            aids, curves = cb(assets, losses_by_aid)
            if len(aids):
                # strip "rlz-" from rlzname below
                result[cb.index, int(rlzname[4:])] = aids, curves
    return result


def _aggregate(outputs, compositemodel, agg, ass, idx, result, monitor):
    # update the result dictionary and the agg array with each output
    L = len(compositemodel.lti)
    I = monitor.insured_losses + 1
    for outs in outputs:
        r = outs.r
        aggr = agg[r]  # array of zeros of shape (E, L, I)
        assr = AccumDict(accum=numpy.zeros((L, I), F32))
        for l, out in enumerate(outs):
            if out is None:  # for GMFs below the minimum_intensity
                continue
            loss_ratios, eids = out
            loss_type = compositemodel.loss_types[l]
            indices = numpy.array([idx[eid] for eid in eids])
            for i, asset in enumerate(outs.assets):
                ratios = loss_ratios[i]
                aid = asset.ordinal
                losses = ratios * asset.value(loss_type)

                # average losses
                if monitor.avg_losses:
                    result['avglosses'][l, r][aid] += (
                        ratios.sum(axis=0) * monitor.ses_ratio)

                # asset losses
                if monitor.loss_ratios:
                    for eid, loss in zip(eids, ratios):
                        if loss.sum() > 0:
                            assr[eid, aid][l] += loss

                # agglosses
                aggr[indices, l] += losses

        # asset losses
        if monitor.loss_ratios:
            ass[r].append(numpy.array([
                (eid, aid, loss) for (eid, aid), loss in assr.items()
            ], monitor.ela_dt))


def event_based_risk(riskinput, riskmodel, assetcol, monitor):
    """
    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param assetcol:
        AssetCollection instance
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary of numpy arrays of shape (L, R)
    """
    A = len(assetcol)
    I = monitor.insured_losses + 1
    eids = riskinput.eids
    E = len(eids)
    L = len(riskmodel.lti)
    idx = dict(zip(eids, range(E)))
    agg = AccumDict(accum=numpy.zeros((E, L, I), F32))  # r -> array
    ass = AccumDict(accum=[])
    result = dict(agglosses=AccumDict(), asslosses=AccumDict())
    if monitor.avg_losses:
        result['avglosses'] = AccumDict(accum=numpy.zeros((A, I), F64))

    outputs = riskmodel.gen_outputs(riskinput, monitor, assetcol)
    _aggregate(outputs, riskmodel, agg, ass, idx, result, monitor)
    for r in sorted(agg):
        records = [(eids[i], loss) for i, loss in enumerate(agg[r])
                   if loss.sum() > 0]
        if records:
            result['agglosses'][r] = numpy.array(records, monitor.elt_dt)
    for r in ass:
        if ass[r]:
            result['asslosses'][r] = numpy.concatenate(ass[r])

    # store the size of the GMFs
    result['gmfbytes'] = monitor.gmfbytes
    return result


@base.calculators.add('event_based_risk')
class EbrPostCalculator(base.RiskCalculator):
    pre_calculator = 'ebrisk'

    def cb_inputs(self, table):
        loss_table = self.datastore[table]
        cbs = self.riskmodel.curve_builders
        return [(cbs, rlzstr, loss_table[rlzstr].value)
                for rlzstr in loss_table]

    def execute(self):
        A = len(self.assetcol)
        ltypes = self.riskmodel.loss_types
        I = self.oqparam.insured_losses + 1
        R = len(self.rlzs_assoc.realizations)
        self.vals = self.assetcol.values()

        # loss curves
        multi_lr_dt = numpy.dtype(
            [(ltype, (F32, len(cbuilder.ratios)))
             for ltype, cbuilder in zip(
                ltypes, self.riskmodel.curve_builders)])
        rcurves = numpy.zeros((A, R, I), multi_lr_dt)

        # build rcurves-rlzs
        if self.oqparam.loss_ratios:
            assets = list(self.assetcol)
            cb_inputs = self.cb_inputs('all_loss_ratios')
            mon = self.monitor('build_rcurves')
            res = parallel.Starmap.apply(
                build_rcurves, (cb_inputs, assets, mon)).reduce()
            for l, r in res:
                aids, curves = res[l, r]
                rcurves[ltypes[l]][aids, r] = curves
            self.datastore['rcurves-rlzs'] = rcurves

        # build rcurves-stats (sequentially)
        # this is a fundamental output, being used to compute loss_maps-stats
        if R > 1:
            weights = self.datastore['realizations']['weight']
            quantiles = self.oqparam.quantile_loss_curves
            if 'avg_losses-rlzs' in self.datastore:
                with self.monitor('computing avg_losses-stats'):
                    self.datastore['avg_losses-stats'] = compute_stats2(
                        self.datastore['avg_losses-rlzs'], quantiles, weights)
            if self.oqparam.loss_ratios:
                with self.monitor('computing rcurves-stats'):
                    self.datastore['rcurves-stats'] = compute_stats2(
                        rcurves, quantiles, weights)

        # build an aggregate loss curve per realization
        if 'agg_loss_table' in self.datastore:
            with self.monitor('building agg_curve'):
                self.build_agg_curve()

    def post_execute(self):
        pass

    def build_agg_curve(self):
        """
        Build a single loss curve per realization. It is NOT obtained
        by aggregating the loss curves; instead, it is obtained without
        generating the loss curves, directly from the the aggregate losses.
        """
        oq = self.oqparam
        cr = {cb.loss_type: cb.curve_resolution
              for cb in self.riskmodel.curve_builders}
        loss_curve_dt, _ = scientific.build_loss_dtypes(
            cr, oq.conditional_loss_poes)
        lts = self.riskmodel.loss_types
        cb_inputs = self.cb_inputs('agg_loss_table')
        I = oq.insured_losses + 1
        R = len(self.rlzs_assoc.realizations)
        result = parallel.Starmap.apply(
            build_agg_curve, (cb_inputs, self.monitor('')),
            concurrent_tasks=self.oqparam.concurrent_tasks).reduce()
        agg_curve = numpy.zeros((I, R), loss_curve_dt)
        for l, r, i in result:
            agg_curve[lts[l]][i, r] = result[l, r, i]
        self.datastore['agg_curve-rlzs'] = agg_curve

        if R > 1:  # save stats too
            weights = self.datastore['realizations']['weight']
            Q1 = len(oq.quantile_loss_curves) + 1
            agg_curve_stats = numpy.zeros((I, Q1), agg_curve.dtype)
            for l, loss_type in enumerate(agg_curve.dtype.names):
                acs = agg_curve_stats[loss_type]
                data = agg_curve[loss_type]
                for i in range(I):
                    losses, all_poes = scientific.normalize_curves_eb(
                        [(c['losses'], c['poes']) for c in data[i]])
                    acs['losses'][i] = losses
                    acs['poes'][i] = compute_stats(
                        all_poes, oq.quantile_loss_curves, weights)
                    acs['avg'][i] = compute_stats(
                        data['avg'][i], oq.quantile_loss_curves, weights)

            self.datastore['agg_curve-stats'] = agg_curve_stats


elt_dt = numpy.dtype([('eid', U32), ('loss', F32)])

save_events = event_based.EventBasedRuptureCalculator.__dict__['save_events']


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


@base.calculators.add('ebrisk')
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
        rlzs_assoc = csm_info.get_rlzs_assoc(
            count_ruptures=lambda grp: len(ruptures_by_grp.get(grp.id, [])))
        num_events = sum(ebr.multiplicity for grp in ruptures_by_grp
                         for ebr in ruptures_by_grp[grp])
        seeds = self.oqparam.random_seed + numpy.arange(num_events)

        allargs = []
        # prepare the risk inputs
        ruptures_per_block = self.oqparam.ruptures_per_block
        start = 0
        grp_trt = csm_info.grp_trt()
        ignore_covs = self.oqparam.ignore_covs
        for grp_id in grp_ids:
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
                ri = riskinput.RiskInputFromRuptures(
                    grp_trt[grp_id], rlzs_assoc, imts, sitecol,
                    rupts, trunc_level, correl_model, min_iml, eps)
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
        correl_model = oq.get_correl_model()
        min_iml = self.get_min_iml(oq)
        imts = list(oq.imtls)
        ela_dt, elt_dt = build_el_dtypes(
            self.riskmodel.loss_types, oq.insured_losses)
        csm_info = self.datastore['csm_info']
        for sm in csm_info.source_models:
            monitor = self.monitor.new(
                ses_ratio=oq.ses_ratio,
                ela_dt=ela_dt, elt_dt=elt_dt,
                loss_ratios=oq.loss_ratios,
                avg_losses=oq.avg_losses,
                insured_losses=oq.insured_losses,
                ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
                maximum_distance=oq.maximum_distance,
                samples=sm.samples,
                seed=self.oqparam.random_seed)
            yield (sm.ordinal, ruptures_by_grp, self.sitecol.complete,
                   self.assetcol, self.riskmodel, imts, oq.truncation_level,
                   correl_model, min_iml, monitor)

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

        ruptures_by_grp = (
            self.precalc.result if self.precalc
            else event_based.get_ruptures_by_grp(self.datastore.parent))
        # the ordering of the ruptures is essential for repeatibility
        for grp in ruptures_by_grp:
            ruptures_by_grp[grp].sort(key=operator.attrgetter('serial'))
        num_rlzs = 0
        allres = []
        source_models = self.csm.info.source_models
        self.sm_by_grp = self.csm.info.get_sm_by_grp()
        for i, args in enumerate(self.gen_args(ruptures_by_grp)):
            ires = self.start_tasks(*args)
            allres.append(ires)
            ires.rlz_slice = slice(num_rlzs, num_rlzs + ires.num_rlzs)
            num_rlzs += ires.num_rlzs
            for sg in source_models[i].src_groups:
                sg.eff_ruptures = ires.num_ruptures.get(sg.id, 0)
        self.datastore['csm_info'] = self.csm.info
        self.datastore.flush()  # when killing the computation
        # the csm_info arrays were stored but not the attributes;
        # adding the .flush() solved the issue
        num_events = self.save_results(allres, num_rlzs)
        self.save_data_transfer(parallel.IterResult.sum(allres))
        return num_events  # {sm_id: #events}

    def save_results(self, allres, num_rlzs):
        """
        :param allres: an iterable of result iterators
        :param num_rlzs: the total number of realizations
        :returns: the total number of events
        """
        self.L = len(self.riskmodel.lti)
        self.R = num_rlzs
        self.T = len(self.assetcol.taxonomies)
        self.A = len(self.assetcol)
        self.I = I = self.oqparam.insured_losses + 1
        avg_losses = self.oqparam.avg_losses
        if avg_losses:
            # since we are using a composite array, we must use fillvalue=None
            # and then set the array to 0 manually (to avoid bogus numbers)
            zero = numpy.zeros(self.A, (F32, (I,)))
            dset = self.datastore.create_dset(
                'avg_losses-rlzs', (F32, (I,)), (self.A, self.R, self.L),
                fillvalue=None)
            for r in range(self.R):
                for l in range(self.L):
                    dset[:, r, l] = zero

        num_events = collections.Counter()
        self.gmfbytes = 0
        for res in allres:
            start, stop = res.rlz_slice.start, res.rlz_slice.stop
            for dic in res:
                if avg_losses:
                    self.save_avg_losses(dset, dic.pop('avglosses'), start)
                self.gmfbytes += dic.pop('gmfbytes')
                self.save_losses(
                    dic.pop('agglosses'), dic.pop('asslosses'), start)
            logging.debug(
                'Saving results for source model #%d, realizations %d:%d',
                res.sm_id + 1, start, stop)
            if hasattr(res, 'ruptures_by_grp'):
                save_events(self, res.ruptures_by_grp)
            num_events[res.sm_id] += res.num_events
        self.datastore['events'].attrs['num_events'] = sum(num_events.values())
        return num_events

    def save_avg_losses(self, dset, dic, start):
        """
        Save a dictionary (l, r) -> losses of average losses
        """
        with self.monitor('saving avg_losses-rlzs'):
            for (l, r), losses in dic.items():
                vs = self.vals[self.riskmodel.loss_types[l]]
                new = numpy.array([losses[:, i] * vs for i in range(self.I)])
                dset[:, r + start, l] += new.T  # shape (A, I)

    def save_losses(self, agglosses, asslosses, offset):
        """
        Save the event loss tables incrementally.

        :param agglosses: a dictionary r -> (eid, loss)
        :param asslosses: a dictionary lr -> (eid, aid, loss)
        :param offset: realization offset
        """
        with self.monitor('saving event loss tables', autoflush=True):
            for r in agglosses:
                key = 'agg_loss_table/rlz-%03d' % (r + offset)
                self.datastore.extend(key, agglosses[r])
            for r in asslosses:
                key = 'all_loss_ratios/rlz-%03d' % (r + offset)
                self.datastore.extend(key, asslosses[r])

    def post_execute(self, num_events):
        """
        Save an array of losses by taxonomy of shape (T, L, R).
        """
        event_based.EventBasedRuptureCalculator.__dict__['post_execute'](
            self, num_events)
        if self.gmfbytes == 0:
            raise RuntimeError('No GMFs were generated, perhaps they were '
                               'all below the minimum_intensity threshold')
        logging.info('Generated %s of GMFs', humansize(self.gmfbytes))
        self.datastore.save('job_info', {'gmfbytes': self.gmfbytes})

        A, E = len(self.assetcol), sum(num_events.values())
        if 'all_loss_ratios' in self.datastore:
            for rlzname in self.datastore['all_loss_ratios']:
                self.datastore.set_nbytes('all_loss_ratios/' + rlzname)
            self.datastore.set_nbytes('all_loss_ratios')
            asslt = self.datastore['all_loss_ratios']
            for rlz, dset in asslt.items():
                dset.attrs['nonzero_fraction'] = len(dset) / (A * E)

        if 'agg_loss_table' not in self.datastore:
            logging.warning(
                'No losses were generated: most likely there is an error in y'
                'our input files or the GMFs were below the minimum intensity')
        else:
            for rlzname in self.datastore['agg_loss_table']:
                self.datastore.set_nbytes('agg_loss_table/' + rlzname)
            self.datastore.set_nbytes('agg_loss_table')
            agglt = self.datastore['agg_loss_table']
            for rlz, dset in agglt.items():
                dset.attrs['nonzero_fraction'] = len(dset) / E
