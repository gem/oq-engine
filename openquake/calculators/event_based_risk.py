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
    AccumDict, block_splitter, split_in_blocks)
from openquake.baselib import parallel
from openquake.risklib import riskinput
from openquake.commonlib import calc
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


def build_rup_loss_table(dstore):
    """
    Save the total losses by rupture.
    """
    oq = dstore['oqparam']
    loss_dt = oq.loss_dt()
    events = dstore['events']
    rup_by_eid = dict(zip(events['eid'], events['rup_id']))
    losses_by_rup = {}
    for rec in dstore['agg_loss_table'].value:  # .value is essential for speed
        rupid = rup_by_eid[rec['eid']]
        if rupid in losses_by_rup:
            losses_by_rup[rupid] += rec['loss']
        else:
            losses_by_rup[rupid] = rec['loss']
    assert losses_by_rup, 'Empty agg_loss_table'
    serials = dstore['ruptures']['serial']
    tbl = numpy.zeros(len(serials), oq.loss_dt())
    for i, serial in enumerate(serials):
        row = tbl[i]
        try:
            for l, lt in enumerate(loss_dt.names):
                row[lt] = losses_by_rup[serial][l]
        except KeyError:
            pass
    return tbl


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

    # update the result dictionary and the agg array with each output
    for out in riskmodel.gen_outputs(riskinput, monitor):
        r = out.rlzi
        idx = riskinput.hazard_getter.eid2idx
        for l, loss_ratios in enumerate(out):
            if loss_ratios is None:  # for GMFs below the minimum_intensity
                continue
            loss_type = riskmodel.loss_types[l]
            indices = numpy.array([idx[eid] for eid in out.eids])

            for a, asset in enumerate(out.assets):
                ratios = loss_ratios[a]  # shape (E, I)
                aid = asset.ordinal
                losses = ratios * asset.value(loss_type)

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
                    # this is the critical loop: it is import to keep it
                    # vectorized in terms of the event indices
                    agg[indices, r, li] += losses[:, i]
                    if param['asset_loss_table']:
                        for eid, ratio in zip(out.eids, ratios[:, i]):
                            if ratio > 0:
                                ass.append((aid, r, eid, li, ratio))

    # collect agglosses
    if param.get('gmf_ebrisk'):
        idx = agg.nonzero()  # return only the nonzero values
        result['agglosses'] = (idx, agg[idx])
    else:  # event_based_risk
        it = ((eid, r, losses)
              for eid, all_losses in zip(eids, agg)
              for r, losses in enumerate(all_losses) if losses.sum())
        result['agglosses'] = numpy.fromiter(it, param['elt_dt'])

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

    # store info about the GMFs, must be done at the end
    result['gmdata'] = riskinput.gmdata
    return result


save_ruptures = event_based.EventBasedRuptureCalculator.__dict__[
    'save_ruptures']


@base.calculators.add('event_based_risk')
class EbriskCalculator(base.RiskCalculator):
    """
    Event based PSHA calculator generating the total losses by taxonomy
    """
    core_task = event_based_risk
    pre_calculator = 'event_based_rupture'
    is_stochastic = True

    def pre_execute(self):
        oq = self.oqparam
        if 'gmfs' in oq.inputs:
            self.pre_calculator = None
        base.RiskCalculator.pre_execute(self)
        if not hasattr(self, 'assetcol'):
            self.assetcol = self.datastore['assetcol']
        self.L = len(self.riskmodel.lti)
        self.T = len(self.assetcol.tagcol)
        self.A = len(self.assetcol)
        self.I = oq.insured_losses + 1
        parent = self.datastore.parent
        self.precomputed_gmfs = 'gmf_data' in parent or 'gmfs' in oq.inputs
        if not self.precomputed_gmfs:
            return
        if 'gmf_data' in parent:
            # read the GMFs from a previous calc
            assert 'gmfs' not in oq.inputs, 'no gmfs_file when using --hc!'
            oqp = parent['oqparam']
            if oqp.investigation_time != oq.investigation_time:
                raise ValueError(
                    'The parent calculation was using investigation_time=%s'
                    ' != %s' % (oqp.investigation_time, oq.investigation_time))
            if oqp.minimum_intensity != oq.minimum_intensity:
                raise ValueError(
                    'The parent calculation was using minimum_intensity=%s'
                    ' != %s' % (oqp.minimum_intensity, oq.minimum_intensity))
            # sorting the eids is essential to get the epsilons in the right
            # order (i.e. consistent with the one used in ebr from ruptures)
            self.eids = sorted(parent['events']['eid'])
            self.datastore['csm_info'] = parent['csm_info']
            self.rlzs_assoc = parent['csm_info'].get_rlzs_assoc()
            self.R = len(self.rlzs_assoc.realizations)
        else:  # read the GMFs from a file
            with self.monitor('reading GMFs', measuremem=True):
                fname = oq.inputs['gmfs']
                sids = self.sitecol.complete.sids
                if fname.endswith('.xml'):  # old approach
                    self.eids, self.R = base.get_gmfs(self)
                else:  # import csv
                    self.eids, self.R, self.gmdata = base.import_gmfs(
                        self.datastore, fname, sids)
                    event_based.save_gmdata(self, self.R)
        self.E = len(self.eids)
        eps = self.epsilon_getter()()
        self.riskinputs = self.build_riskinputs('gmf', eps, self.E)
        self.param['gmf_ebrisk'] = True
        self.param['insured_losses'] = oq.insured_losses
        self.param['avg_losses'] = oq.avg_losses
        self.param['ses_ratio'] = oq.ses_ratio
        self.param['asset_loss_table'] = oq.asset_loss_table
        self.param['elt_dt'] = numpy.dtype(
            [('eid', U64), ('rlzi', U16), ('loss', (F32, (self.L * self.I,)))])
        self.taskno = 0
        self.start = 0
        avg_losses = self.oqparam.avg_losses
        if avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, self.R, self.L * self.I))
        self.agglosses = numpy.zeros((self.E, self.R, self.L * self.I), F32)
        self.vals = self.assetcol.values()
        self.num_losses = numpy.zeros((self.A, self.R), U32)
        if oq.asset_loss_table:
            # save all_loss_ratios
            self.alr_nbytes = 0
            self.indices = collections.defaultdict(list)  # sid -> pairs

    # TODO: if the number of source models is larger than concurrent_tasks
    # a different strategy should be used; the one used here is good when
    # there are few source models, so that we cannot parallelize on those
    def start_tasks(self, sm_id, sitecol, assetcol, riskmodel, imtls,
                    trunc_level, correl_model, min_iml, monitor):
        """
        :param sm_id: source model ordinal
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
        sm_info = self.csm_info.get_info(sm_id)
        grp_ids = sorted(sm_info.get_sm_by_grp())
        rlzs_assoc = sm_info.get_rlzs_assoc()
        # prepare the risk inputs
        allargs = []
        ruptures_per_block = self.oqparam.ruptures_per_block
        try:
            csm_info = self.csm.info
        except AttributeError:  # there is no .csm if --hc was given
            csm_info = self.datastore['csm_info']
        samples_by_grp = csm_info.get_samples_by_grp()
        num_events = 0
        num_ruptures = {}
        for grp_id in grp_ids:
            rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(grp_id)
            samples = samples_by_grp[grp_id]
            ruptures = self.ruptures_by_grp.get(grp_id, [])
            num_ruptures[grp_id] = len(ruptures)
            from_parent = hasattr(ruptures, 'split')
            if from_parent:  # read the ruptures from the parent datastore
                logging.info('Reading ruptures group #%d', grp_id)
                with self.monitor('reading ruptures', measuremem=True):
                    blocks = ruptures.split(ruptures_per_block)
            else:  # the ruptures are already in memory
                blocks = block_splitter(ruptures, ruptures_per_block)
            for rupts in blocks:
                n_events = (rupts.n_events if from_parent
                            else sum(ebr.multiplicity for ebr in rupts))
                eps = self.get_eps(self.start, self.start + n_events)
                num_events += n_events
                self.start += n_events
                getter = getters.GmfGetter(
                    rlzs_by_gsim, rupts, sitecol, imtls, min_iml,
                    self.oqparam.maximum_distance, trunc_level, correl_model,
                    samples)
                ri = riskinput.RiskInput(getter, self.assets_by_site, eps)
                allargs.append((ri, riskmodel, assetcol, monitor))

        self.vals = self.assetcol.values()
        taskname = '%s#%d' % (event_based_risk.__name__, sm_id + 1)
        if self.datastore.parent:  # avoid hdf5 fork issues
            self.datastore.parent.close()
        ires = parallel.Starmap(
            event_based_risk, allargs, name=taskname).submit_all()
        ires.num_ruptures = num_ruptures
        ires.num_events = num_events
        ires.num_rlzs = len(rlzs_assoc.realizations)
        ires.sm_id = sm_id
        return ires

    def gen_args(self):
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
                ses_ratio=oq.ses_ratio,
                loss_dt=oq.loss_dt(), elt_dt=elt_dt,
                asset_loss_table=oq.asset_loss_table,
                avg_losses=oq.avg_losses,
                insured_losses=oq.insured_losses,
                ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
                maximum_distance=oq.maximum_distance,
                samples=sm.samples,
                seed=self.oqparam.random_seed)
            yield (sm.ordinal, self.sitecol.complete,
                   param, self.riskmodel, imtls, oq.truncation_level,
                   correl_model, min_iml, mon)

    def epsilon_getter(self):
        """
        :returns: a callable (start, stop) producing a slice of epsilons
        """
        return riskinput.make_epsilon_getter(
            len(self.assetcol), self.E,
            self.oqparam.asset_correlation,
            self.oqparam.master_seed,
            self.oqparam.ignore_covs or not self.riskmodel.covs)

    def execute(self):
        """
        Run the calculator and aggregate the results
        """
        if self.precomputed_gmfs:
            return base.RiskCalculator.execute(self)

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
            # event based risk calculation already done, postprocess
            EbrPostCalculator(self).run(close=False)
            return

        self.csm_info = self.datastore['csm_info']
        if self.precalc:
            self.ruptures_by_grp = self.precalc.result
            # the ordering of the ruptures is essential for repeatibility
            for grp in self.ruptures_by_grp:
                self.ruptures_by_grp[grp].sort(
                    key=operator.attrgetter('serial'))
        else:  # there is a parent calculation
            self.ruptures_by_grp = getters.RuptureGetter.from_(
                self.datastore.parent)
        num_rlzs = 0
        allres = []
        source_models = self.csm_info.source_models
        self.sm_by_grp = self.csm_info.get_sm_by_grp()
        self.E = num_events = len(self.datastore['events'])
        self.assets_by_site = self.assetcol.assets_by_site()
        self.start = 0
        self.get_eps = self.epsilon_getter()
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        for i, args in enumerate(self.gen_args()):
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
            if hasattr(res, 'eff_ruptures'):  # for UCERF
                self.eff_ruptures += res.eff_ruptures
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
            if self.precomputed_gmfs:
                idx, agg = agglosses
                self.agglosses[idx] += agg
            else:  # event_based_risk
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
                vs = self.vals[self.riskmodel.loss_types[l]]
                if self.precomputed_gmfs:  # there is no offset
                    self.dset[aids, r, li] += numpy.array(
                        [ratios.get(aid, 0) * vs[aid] for aid in aids])
                else:  # all assets
                    self.dset[:, r + offset, li] += ratios * vs
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
        if self.precomputed_gmfs:
            logging.info('Saving event loss table')
            with self.monitor('saving event loss table', measuremem=True):
                # saving zeros is a lot faster than adding an `if loss.sum()`
                agglosses = numpy.fromiter(
                    ((e, r, loss)
                     for e, losses in zip(self.eids, self.agglosses)
                     for r, loss in enumerate(losses) if loss.sum()),
                    self.param['elt_dt'])
                self.datastore['agg_loss_table'] = agglosses
        else:
            num_events = result
            # gmv[:-2] are the total gmv per each IMT
            gmv = sum(gm[:-2].sum() for gm in self.gmdata.values())
            if not gmv:
                raise RuntimeError('No GMFs were generated, perhaps they were '
                                   'all below the minimum_intensity threshold')

            if 'agg_loss_table' not in self.datastore:
                logging.warning(
                    'No losses were generated: most likely there is an error '
                    'in y our input files or the GMFs were below the minimum '
                    'intensity')
            else:
                self.datastore.set_nbytes('agg_loss_table')
                E = sum(num_events.values())
                agglt = self.datastore['agg_loss_table']
                agglt.attrs['nonzero_fraction'] = len(agglt) / E

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
        b = get_loss_builder(dstore)
        if 'ruptures' in dstore:
            logging.info('Building rup_loss_table')
            with self.monitor('building rup_loss_table', measuremem=True):
                dstore['rup_loss_table'] = rlt = build_rup_loss_table(dstore)
                ridx = [rlt[lt].argmax() for lt in oq.loss_dt().names]
                dstore.set_attrs('rup_loss_table', ridx=ridx)
        stats = oq.risk_stats()
        logging.info('Building aggregate loss curves')
        with self.monitor('building agg_curves', measuremem=True):
            array, array_stats = b.build(dstore['agg_loss_table'].value, stats)
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
        self.R = calc.R
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
