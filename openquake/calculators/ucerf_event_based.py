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
from openquake.hazardlib.contexts import ContextMaker, FarAwayRupture
from openquake.hazardlib.source.rupture import EBRupture
from openquake.risklib import riskinput
from openquake.commonlib import calc, util
from openquake.calculators import base, event_based, getters
from openquake.calculators.ucerf_base import (
    DEFAULT_TRT, UcerfFilter, generate_background_ruptures,
    get_composite_source_model)
from openquake.calculators.event_based_risk import (
    EbrCalculator, event_based_risk)

U16 = numpy.uint16
U64 = numpy.uint64
F32 = numpy.float32
TWO16 = 2 ** 16


def generate_event_set(ucerf, background_sids, src_filter, seed):
    """
    Generates the event set corresponding to a particular branch
    """
    # get rates from file
    with h5py.File(ucerf.source_file, 'r') as hdf5:
        occurrences = ucerf.tom.sample_number_of_occurrences(
            ucerf.rate, seed)
        indices = numpy.where(occurrences)[0]
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
    return ruptures, rupture_occ


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
def compute_ruptures(sources, src_filter, gsims, param, monitor):
    """
    :param sources: a list with a single UCERF source
    :param src_filter: a SourceFilter instance
    :param gsims: a list of GSIMs
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
    ebruptures = []
    background_sids = src.get_background_sids(src_filter)
    sitecol = src_filter.sitecol
    cmaker = ContextMaker(gsims, src_filter.integration_distance)
    for sample in range(param['samples']):
        for ses_idx, ses_seed in param['ses_seeds']:
            seed = sample * TWO16 + ses_seed
            with sampl_mon:
                rups, n_occs = generate_event_set(
                    src, background_sids, src_filter, seed)
            with filt_mon:
                for rup, n_occ in zip(rups, n_occs):
                    rup.serial = serial
                    rup.seed = seed
                    try:
                        rup.sctx, rup.dctx = cmaker.make_contexts(sitecol, rup)
                        indices = rup.sctx.sids
                    except FarAwayRupture:
                        continue
                    events = []
                    for _ in range(n_occ):
                        events.append((0, src.src_group_id, ses_idx, sample))
                    if events:
                        evs = numpy.array(events, stochastic.event_dt)
                        ebruptures.append(EBRupture(rup, indices, evs))
                        serial += 1
    res.num_events = len(stochastic.set_eids(ebruptures))
    res[src.src_group_id] = ebruptures
    if not param['save_ruptures']:
        res.events_by_grp = {grp_id: event_based.get_events(res[grp_id])
                             for grp_id in res}
    res.eff_ruptures = {src.src_group_id: src.num_ruptures}
    return res


@base.calculators.add('ucerf_rupture')
class UCERFRuptureCalculator(event_based.EventBasedRuptureCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_task = compute_ruptures

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        logging.warn('%s is still experimental', self.__class__.__name__)
        oq = self.oqparam
        self.read_risk_data()  # read the site collection
        self.csm = get_composite_source_model(oq)
        self.csm.src_filter = UcerfFilter(self.sitecol, oq.maximum_distance)
        logging.info('Found %d source model logic tree branches',
                     len(self.csm.source_models))
        self.datastore['sitecol'] = self.sitecol
        self.datastore['csm_info'] = self.csm_info = self.csm.info
        self.rlzs_assoc = self.csm_info.get_rlzs_assoc()
        self.infos = []
        self.eid = collections.Counter()  # sm_id -> event_id
        self.sm_by_grp = self.csm_info.get_sm_by_grp()
        if not self.oqparam.imtls:
            raise ValueError('Missing intensity_measure_types!')
        self.rupser = calc.RuptureSerializer(self.datastore)
        self.precomputed_gmfs = False

    def gen_args(self, csm, monitor):
        """
        Generate a task for each branch
        """
        oq = self.oqparam
        allargs = []  # it is better to return a list; if there is single
        # branch then `parallel.Starmap` will run the task in core
        for sm_id in range(len(csm.source_models)):
            ssm = csm.get_model(sm_id)
            [sm] = ssm.source_models
            gsims = ssm.gsim_lt.values[DEFAULT_TRT]
            srcs = ssm.get_sources()
            for ses_idx in range(1, oq.ses_per_logic_tree_path + 1):
                ses_seeds = [(ses_idx, oq.ses_seed + ses_idx)]
                param = dict(ses_seeds=ses_seeds, samples=sm.samples,
                             save_ruptures=oq.save_ruptures,
                             filter_distance=oq.filter_distance)
                allargs.append(
                    (srcs, self.csm.src_filter, gsims, param, monitor))
        return allargs


class List(list):
    """Trivial container returned by compute_losses"""


@util.reader
def compute_losses(ssm, src_filter, param, riskmodel,
                   imts, trunc_level, correl_model, min_iml, monitor):
    """
    Compute the losses for a single source model. Returns the ruptures
    as an attribute `.ruptures_by_grp` of the list of losses.

    :param ssm: CompositeSourceModel containing a single source model
    :param sitecol: a SiteCollection instance
    :param param: a dictionary of parameters
    :param riskmodel: a RiskModel instance
    :param imts: a list of Intensity Measure Types
    :param trunc_level: truncation level
    :param correl_model: correlation model
    :param min_iml: vector of minimum intensities, one per IMT
    :param monitor: a Monitor instance
    :returns: a List containing the losses by taxonomy and some attributes
    """
    [grp] = ssm.src_groups
    res = List()
    gsims = ssm.gsim_lt.values[DEFAULT_TRT]
    ruptures_by_grp = compute_ruptures(
        grp, src_filter, gsims, param, monitor)
    [(grp_id, ebruptures)] = ruptures_by_grp.items()
    rlzs_assoc = ssm.info.get_rlzs_assoc()
    samples = ssm.info.get_samples_by_grp()
    num_rlzs = len(rlzs_assoc.realizations)
    rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(DEFAULT_TRT)
    getter = getters.GmfGetter(
        rlzs_by_gsim, ebruptures, src_filter.sitecol, imts, min_iml,
        src_filter.integration_distance, trunc_level, correl_model,
        samples[grp_id])
    ri = riskinput.RiskInput(getter, param['assetcol'].assets_by_site())
    res.append(event_based_risk(ri, riskmodel, param, monitor))
    res.sm_id = ssm.sm_id
    res.num_events = len(ri.hazard_getter.eids)
    start = res.sm_id * num_rlzs
    res.rlz_slice = slice(start, start + num_rlzs)
    res.events_by_grp = ruptures_by_grp.events_by_grp
    res.eff_ruptures = ruptures_by_grp.eff_ruptures
    return res


@base.calculators.add('ucerf_hazard')
class UCERFHazardCalculator(event_based.EventBasedCalculator):
    """
    Runs a standard event based calculation starting from UCERF ruptures
    """
    pre_calculator = 'ucerf_rupture'


@base.calculators.add('ucerf_risk')
class UCERFRiskCalculator(EbrCalculator):
    """
    Event based risk calculator for UCERF, parallelizing on the source models
    """
    pre_execute = UCERFRuptureCalculator.__dict__['pre_execute']

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
        imts = list(oq.imtls)
        elt_dt = numpy.dtype([('eid', U64), ('rlzi', U16),
                              ('loss', (F32, (self.L, self.I)))])
        monitor = self.monitor('compute_losses')
        for sm in self.csm.source_models:
            if sm.samples > 1:
                logging.warn('Sampling in ucerf_risk is untested')
            ssm = self.csm.get_model(sm.ordinal)
            for ses_idx in range(1, oq.ses_per_logic_tree_path + 1):
                param = dict(ses_seeds=[(ses_idx, oq.ses_seed + ses_idx)],
                             samples=sm.samples, assetcol=self.assetcol,
                             save_ruptures=False,
                             ses_ratio=oq.ses_ratio,
                             avg_losses=oq.avg_losses,
                             elt_dt=elt_dt,
                             asset_loss_table=False,
                             insured_losses=oq.insured_losses)
                yield (ssm, self.csm.src_filter, param,
                       self.riskmodel, imts, oq.truncation_level,
                       correl_model, min_iml, monitor)

    def execute(self):
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        num_rlzs = len(self.rlzs_assoc.realizations)
        self.grp_trt = self.csm_info.grp_by("trt")
        res = parallel.Starmap(compute_losses, self.gen_args()).submit_all()
        self.vals = self.assetcol.values()
        self.eff_ruptures = AccumDict(accum=0)
        num_events = self.save_results(res, num_rlzs)
        self.csm.info.update_eff_ruptures(self.eff_ruptures)
        self.datastore['csm_info'] = self.csm.info
        return num_events
