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
import collections
import numpy
import h5py

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip
from openquake.baselib import parallel
from openquake.hazardlib.calc import stochastic
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.contexts import ContextMaker
from openquake.risklib import riskinput
from openquake.commonlib import util
from openquake.calculators import base, event_based, getters
from openquake.calculators.ucerf_base import (
    DEFAULT_TRT, UcerfFilter, generate_background_ruptures)
from openquake.calculators.event_based_risk import EbrCalculator
from openquake.calculators.export.loss_curves import get_loss_builder

U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16

save_ruptures = event_based.EventBasedCalculator.save_ruptures


def ucerf_risk(riskinput, riskmodel, param, monitor):
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
    with monitor('getting hazard'):
        riskinput.hazard_getter.init()
        hazard = riskinput.hazard_getter.get_hazard()
    eids = riskinput.hazard_getter.eids
    A = len(riskinput.aids)
    E = len(eids)
    assert not param['insured_losses']
    L = len(riskmodel.lti)
    R = riskinput.hazard_getter.num_rlzs
    param['lrs_dt'] = numpy.dtype([('rlzi', U16), ('ratios', (F32, L))])
    agg = numpy.zeros((E, R, L), F32)
    avg = numpy.zeros((A, R, L), F32)
    result = dict(aids=riskinput.aids, avglosses=avg)

    # update the result dictionary and the agg array with each output
    for out in riskmodel.gen_outputs(riskinput, monitor, hazard):
        if len(out.eids) == 0:  # this happens for sites with no events
            continue
        r = out.rlzi
        idx = riskinput.hazard_getter.eid2idx
        for l, loss_ratios in enumerate(out):
            if loss_ratios is None:  # for GMFs below the minimum_intensity
                continue
            loss_type = riskmodel.loss_types[l]
            indices = numpy.array([idx[eid] for eid in out.eids])
            for a, asset in enumerate(out.assets):
                ratios = loss_ratios[a]  # shape (E, 1)
                aid = asset.ordinal
                losses = ratios * asset.value(loss_type)
                # average losses
                if param['avg_losses']:
                    avg[aid, :, :] = losses.sum(axis=0) * param['ses_ratio']

                # this is the critical loop: it is important to keep it
                # vectorized in terms of the event indices
                agg[indices, r, l] += losses[:, 0]  # 0 == no insured

    it = ((eid, r, losses)
          for eid, all_losses in zip(eids, agg)
          for r, losses in enumerate(all_losses) if losses.sum())
    result['agglosses'] = numpy.fromiter(it, param['elt_dt'])
    # store info about the GMFs, must be done at the end
    result['gmdata'] = riskinput.gmdata
    return result


def generate_event_set(ucerf, background_sids, src_filter, seed):
    """
    Generates the event set corresponding to a particular branch
    """
    # get rates from file
    with h5py.File(ucerf.source_file, 'r') as hdf5:
        occurrences = ucerf.tom.sample_number_of_occurrences(
            ucerf.rate, seed)
        indices, = numpy.where(occurrences)
        logging.debug(
            'Considering "%s", %d ruptures', ucerf.source_id, len(indices))

        # get ruptures from the indices
        ruptures = []
        rupture_occ = []
        for iloc, n_occ in zip(indices, occurrences[indices]):
            ucerf_rup = ucerf.get_ucerf_rupture(iloc, src_filter)
            if ucerf_rup:
                ruptures.append(ucerf_rup)
                rupture_occ.append(n_occ)

        # sample background sources
        background_ruptures, background_n_occ = sample_background_model(
            hdf5, ucerf.idx_set["grid_key"], ucerf.tom, seed,
            background_sids, ucerf.min_mag, ucerf.npd, ucerf.hdd, ucerf.usd,
            ucerf.lsd, ucerf.msr, ucerf.aspect, ucerf.tectonic_region_type)
        ruptures.extend(background_ruptures)
        rupture_occ.extend(background_n_occ)
    return ruptures, numpy.array(rupture_occ, numpy.uint16).reshape(-1, 1, 1)


def sample_background_model(
        hdf5, branch_key, tom, seed, filter_idx, min_mag, npd, hdd,
        upper_seismogenic_depth, lower_seismogenic_depth, msr=WC1994(),
        aspect=1.5, trt=DEFAULT_TRT):
    """
    Generates a rupture set from a sample of the background model

    :param branch_key:
        Key to indicate the branch for selecting the background model
    :param tom:
        Temporal occurrence model as instance of :class:
        openquake.hazardlib.tom.TOM
    :param seed:
        Random seed to use in the call to tom.sample_number_of_occurrences
    :param filter_idx:
        Sites for consideration (can be None!)
    :param float min_mag:
        Minimim magnitude for consideration of background sources
    :param npd:
        Nodal plane distribution as instance of :class:
        openquake.hazardlib.pmf.PMF
    :param hdd:
        Hypocentral depth distribution as instance of :class:
        openquake.hazardlib.pmf.PMF
    :param float aspect:
        Aspect ratio
    :param float upper_seismogenic_depth:
        Upper seismogenic depth (km)
    :param float lower_seismogenic_depth:
        Lower seismogenic depth (km)
    :param msr:
        Magnitude scaling relation
    :param float integration_distance:
        Maximum distance from rupture to site for consideration
    """
    bg_magnitudes = hdf5["/".join(["Grid", branch_key, "Magnitude"])].value
    # Select magnitudes above the minimum magnitudes
    mag_idx = bg_magnitudes >= min_mag
    mags = bg_magnitudes[mag_idx]
    rates = hdf5["/".join(["Grid", branch_key, "RateArray"])][filter_idx, :]
    rates = rates[:, mag_idx]
    valid_locs = hdf5["Grid/Locations"][filter_idx, :]
    # Sample remaining rates
    sampler = tom.sample_number_of_occurrences(rates, seed)
    background_ruptures = []
    background_n_occ = []
    for i, mag in enumerate(mags):
        rate_idx = numpy.where(sampler[:, i])[0]
        rate_cnt = sampler[rate_idx, i]
        occurrence = rates[rate_idx, i]
        locations = valid_locs[rate_idx, :]
        ruptures = generate_background_ruptures(
            tom, locations, occurrence,
            mag, npd, hdd, upper_seismogenic_depth,
            lower_seismogenic_depth, msr, aspect, trt)
        background_ruptures.extend(ruptures)
        background_n_occ.extend(rate_cnt.tolist())
    return background_ruptures, background_n_occ

# #################################################################### #


@util.reader
def compute_hazard(sources, src_filter, rlzs_by_gsim, param, monitor):
    """
    :param sources: a list with a single UCERF source
    :param src_filter: a SourceFilter instance
    :param rlzs_by_gsim: a dictionary gsim -> rlzs
    :param param: extra parameters
    :param monitor: a Monitor instance
    :returns: an AccumDict grp_id -> EBRuptures
    """
    [src] = sources
    res = AccumDict()
    res.calc_times = []
    serial = 1
    sampl_mon = monitor('sampling ruptures', measuremem=True)
    filt_mon = monitor('filtering ruptures', measuremem=False)
    res.trt = DEFAULT_TRT
    background_sids = src.get_background_sids(src_filter)
    sitecol = src_filter.sitecol
    cmaker = ContextMaker(rlzs_by_gsim, src_filter.integration_distance)
    num_ses = param['ses_per_logic_tree_path']
    num_rlzs = sum(len(rlzs) for rlzs in rlzs_by_gsim.values())
    samples = getattr(src, 'samples', 1)
    n_occ = AccumDict(accum=numpy.zeros((samples, num_ses), numpy.uint16))
    with sampl_mon:
        for sam_idx in range(samples):
            for ses_idx, ses_seed in param['ses_seeds']:
                seed = sam_idx * TWO16 + ses_seed
                rups, occs = generate_event_set(
                    src, background_sids, src_filter, seed)
                for rup, occ in zip(rups, occs):
                    n_occ[rup][sam_idx, ses_idx] = occ
                    rup.serial = serial
                    serial += 1
    with filt_mon:
        ebruptures = stochastic.build_eb_ruptures(
            src, slice(0, num_rlzs), num_ses, cmaker, sitecol, n_occ.items())
    res.num_events = sum(ebr.multiplicity for ebr in ebruptures)
    res['ruptures'] = {src.src_group_id: ebruptures}
    if param['save_ruptures']:
        res.ruptures_by_grp = {src.src_group_id: ebruptures}
    else:
        res.events_by_grp = {
            src.src_group_id: event_based.get_events(ebruptures)}
    res.eff_ruptures = {src.src_group_id: src.num_ruptures}
    if param.get('gmf'):
        getter = getters.GmfGetter(
            rlzs_by_gsim, ebruptures, sitecol,
            param['oqparam'], param['min_iml'], samples)
        res.update(getter.compute_gmfs_curves(monitor))
    return res


@base.calculators.add('ucerf_hazard')
class UCERFHazardCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating the ruptures and GMFs together
    """
    core_task = compute_hazard

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        logging.warn('%s is still experimental', self.__class__.__name__)
        self.read_inputs()  # read the site collection
        logging.info('Found %d source model logic tree branches',
                     len(self.csm.source_models))
        self.datastore['sitecol'] = self.sitecol
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc()
        self.eid = collections.Counter()  # sm_id -> event_id
        self.sm_by_grp = self.csm.info.get_sm_by_grp()
        if not self.oqparam.imtls:
            raise ValueError('Missing intensity_measure_types!')
        self.precomputed_gmfs = False

    def from_sources(self, param):
        """
        Generate a task for each branch
        """
        oq = self.oqparam
        allargs = []  # it is better to return a list; if there is single
        # branch then `parallel.Starmap` will run the task in core
        rlzs_by_gsim = self.csm.info.get_rlzs_by_gsim_grp()
        ufilter = UcerfFilter(self.sitecol, self.oqparam.maximum_distance)
        for sm_id in range(len(self.csm.source_models)):
            ssm = self.csm.get_model(sm_id)
            [sm] = ssm.source_models
            srcs = ssm.get_sources()
            for ses_idx in range(oq.ses_per_logic_tree_path):
                param = param.copy()
                param['ses_seeds'] = [(ses_idx, oq.ses_seed + ses_idx + 1)]
                allargs.append((srcs, ufilter, rlzs_by_gsim[sm_id], param))
        return allargs


class List(list):
    """Trivial container returned by compute_losses"""


@util.reader
def compute_losses(ssm, src_filter, param, riskmodel, monitor):
    """
    Compute the losses for a single source model. Returns the ruptures
    as an attribute `.ruptures_by_grp` of the list of losses.

    :param ssm: CompositeSourceModel containing a single source model
    :param sitecol: a SiteCollection instance
    :param param: a dictionary of extra parameters
    :param riskmodel: a RiskModel instance
    :param monitor: a Monitor instance
    :returns: a List containing the losses by taxonomy and some attributes
    """
    [grp] = ssm.src_groups
    res = List()
    rlzs_assoc = ssm.info.get_rlzs_assoc()
    rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(DEFAULT_TRT)
    hazard = compute_hazard(grp, src_filter, rlzs_by_gsim, param, monitor)
    [(grp_id, ebruptures)] = hazard['ruptures'].items()

    samples = ssm.info.get_samples_by_grp()
    num_rlzs = len(rlzs_assoc.realizations)
    rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(DEFAULT_TRT)
    getter = getters.GmfGetter(
        rlzs_by_gsim, ebruptures, src_filter.sitecol,
        param['oqparam'], param['min_iml'], samples[grp_id])
    ri = riskinput.RiskInput(getter, param['assetcol'].assets_by_site())
    res.append(ucerf_risk(ri, riskmodel, param, monitor))
    res.sm_id = ssm.sm_id
    res.num_events = len(ri.hazard_getter.eids)
    start = res.sm_id * num_rlzs
    res.rlz_slice = slice(start, start + num_rlzs)
    res.events_by_grp = hazard.events_by_grp
    res.eff_ruptures = hazard.eff_ruptures
    return res


@base.calculators.add('ucerf_risk')
class UCERFRiskCalculator(EbrCalculator):
    """
    Event based risk calculator for UCERF, parallelizing on the source models
    """
    pre_execute = UCERFHazardCalculator.pre_execute

    def gen_args(self):
        """
        Yield the arguments required by build_ruptures, i.e. the
        source models, the asset collection, the riskmodel and others.
        """
        oq = self.oqparam
        self.L = len(self.riskmodel.lti)
        self.I = oq.insured_losses + 1
        min_iml = self.get_min_iml(oq)
        elt_dt = numpy.dtype([('eid', U64), ('rlzi', U16),
                              ('loss', (F32, (self.L,)))])
        monitor = self.monitor('compute_losses')
        src_filter = UcerfFilter(self.sitecol.complete, oq.maximum_distance)

        for sm in self.csm.source_models:
            ssm = self.csm.get_model(sm.ordinal)
            for ses_idx in range(oq.ses_per_logic_tree_path):
                param = dict(
                    ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
                    ses_seeds=[(ses_idx, oq.ses_seed + ses_idx + 1)],
                    samples=sm.samples, assetcol=self.assetcol,
                    save_ruptures=False,
                    ses_ratio=oq.ses_ratio,
                    avg_losses=oq.avg_losses,
                    elt_dt=elt_dt,
                    min_iml=min_iml,
                    oqparam=oq,
                    insured_losses=oq.insured_losses)
                yield ssm, src_filter, param, self.riskmodel

    def execute(self):
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        num_rlzs = len(self.rlzs_assoc.realizations)
        self.grp_trt = self.csm.info.grp_by("trt")
        res = parallel.Starmap(
            compute_losses, self.gen_args(),
            self.monitor()).submit_all()
        self.eff_ruptures = AccumDict(accum=0)
        num_events = self.save_results(res, num_rlzs)
        self.csm.info.update_eff_ruptures(self.eff_ruptures)
        self.datastore['csm_info'] = self.csm.info
        return num_events

    def save_results(self, allres, num_rlzs):
        """
        :param allres: an iterable of result iterators
        :param num_rlzs: the total number of realizations
        :returns: the total number of events
        """
        oq = self.oqparam
        self.A = len(self.assetcol)
        if oq.avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, num_rlzs, self.L * self.I))

        num_events = collections.Counter()
        self.gmdata = AccumDict(accum=numpy.zeros(len(oq.imtls) + 1, F32))
        self.taskno = 0
        self.start = 0
        for res in allres:
            start, stop = res.rlz_slice.start, res.rlz_slice.stop
            for dic in res:
                for r, arr in dic.pop('gmdata').items():
                    self.gmdata[start + r] += arr
                self.save_losses(dic, start)
            logging.debug(
                'Saving results for source model #%d, realizations %d:%d',
                res.sm_id + 1, start, stop)
            if hasattr(res, 'eff_ruptures'):
                self.eff_ruptures += res.eff_ruptures
            if hasattr(res, 'ruptures_by_grp'):
                for ruptures in res.ruptures_by_grp.values():
                    save_ruptures(self, ruptures)
            elif hasattr(res, 'events_by_grp'):
                for grp_id in res.events_by_grp:
                    events = res.events_by_grp[grp_id]
                    self.datastore.extend('events', events)
            num_events[res.sm_id] += res.num_events
        base.save_gmdata(self, num_rlzs)
        return num_events

    def save_losses(self, dic, offset=0):
        """
        Save the event loss tables incrementally.

        :param dic:
            dictionary with agglosses, assratios, avglosses, lrs_idx
        :param offset:
            realization offset
        """
        with self.monitor('saving event loss table', autoflush=True):
            agglosses = dic.pop('agglosses')
            agglosses['rlzi'] += offset
            self.datastore.extend('losses_by_event', agglosses)
        with self.monitor('saving avg_losses-rlzs'):
            avglosses = dic.pop('avglosses')  # shape (A, R, L)
            A, R, L = avglosses.shape
            for r in range(R):
                self.dset[:, r + offset, :] += avglosses[:, r, :]
        self.taskno += 1

    def post_execute(self, result):
        """
        Call the EbrPostCalculator to compute the aggregate loss curves
        """
        if 'losses_by_event' not in self.datastore:
            logging.warning(
                'No losses were generated: most likely there is an error '
                'in your input files or the GMFs were below the minimum '
                'intensity')
        else:
            self.datastore.set_nbytes('losses_by_event')
            E = sum(result.values())
            agglt = self.datastore['losses_by_event']
            agglt.attrs['nonzero_fraction'] = len(agglt) / E

        self.param = dict(builder=get_loss_builder(self.datastore))
        self.postproc()
