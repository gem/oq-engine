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
import time
import logging
import collections
import numpy
import h5py

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip
from openquake.hazardlib.calc import stochastic
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.source.rupture import EBRupture
from openquake.calculators import base, event_based
from openquake.calculators.ucerf_base import (
    DEFAULT_TRT, generate_background_ruptures)

U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16


def generate_event_set(ucerf, background_sids, src_filter, ses_idx, seed):
    """
    Generates the event set corresponding to a particular branch
    """
    serial = seed + ses_idx * TWO16
    # get rates from file
    with h5py.File(ucerf.source_file, 'r') as hdf5:
        occurrences = ucerf.tom.sample_number_of_occurrences(ucerf.rate, seed)
        indices, = numpy.where(occurrences)
        logging.debug(
            'Considering "%s", %d ruptures', ucerf.source_id, len(indices))

        # get ruptures from the indices
        ruptures = []
        rupture_occ = []
        for iloc, n_occ in zip(indices, occurrences[indices]):
            ucerf_rup = ucerf.get_ucerf_rupture(iloc, src_filter)
            if ucerf_rup:
                ucerf_rup.serial = serial
                serial += 1
                ruptures.append(ucerf_rup)
                rupture_occ.append(n_occ)

        # sample background sources
        background_ruptures, background_n_occ = sample_background_model(
            hdf5, ucerf.idx_set["grid_key"], ucerf.tom, seed,
            background_sids, ucerf.min_mag, ucerf.npd, ucerf.hdd, ucerf.usd,
            ucerf.lsd, ucerf.msr, ucerf.aspect, ucerf.tectonic_region_type)
        for i, brup in enumerate(background_ruptures):
            brup.serial = serial
            serial += 1
            ruptures.append(brup)
        rupture_occ.extend(background_n_occ)

    assert len(ruptures) < TWO16, len(ruptures)  # < 2^16 ruptures per SES
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


def build_ruptures(sources, src_filter, param, monitor):
    """
    :param sources: a list with a single UCERF source
    :param param: extra parameters
    :param monitor: a Monitor instance
    :returns: an AccumDict grp_id -> EBRuptures
    """
    [src] = sources
    res = AccumDict()
    res.calc_times = []
    sampl_mon = monitor('sampling ruptures', measuremem=True)
    res.trt = DEFAULT_TRT
    background_sids = src.get_background_sids(src_filter)
    samples = getattr(src, 'samples', 1)
    n_occ = AccumDict(accum=0)
    t0 = time.time()
    with sampl_mon:
        for sam_idx in range(samples):
            for ses_idx, ses_seed in param['ses_seeds']:
                seed = sam_idx * TWO16 + ses_seed
                rups, occs = generate_event_set(
                    src, background_sids, src_filter, ses_idx, seed)
                for rup, occ in zip(rups, occs):
                    n_occ[rup] += occ
    tot_occ = sum(n_occ.values())
    dic = {'eff_ruptures': {src.src_group_id: src.num_ruptures}}
    eb_ruptures = [EBRupture(rup, src.id, src.src_group_id, n, samples)
                   for rup, n in n_occ.items()]
    dic['rup_array'] = stochastic.get_rup_array(eb_ruptures, src_filter)
    dt = time.time() - t0
    dic['calc_times'] = {src.id: numpy.array([tot_occ, dt], F32)}
    return dic


@base.calculators.add('ucerf_hazard')
class UCERFHazardCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating the ruptures and GMFs together
    """
    build_ruptures = build_ruptures
    accept_precalc = ['ucerf_hazard']

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        logging.warning('%s is still experimental', self.__class__.__name__)
        self.read_inputs()  # read the site collection
        logging.info('Found %d source model logic tree branches',
                     len(self.csm.source_models))
        self.datastore['sitecol'] = self.sitecol
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc()
        self.eid = collections.Counter()  # sm_id -> event_id
        self.sm_by_grp = self.csm.info.get_sm_by_grp()
        self.init_logic_tree(self.csm.info)
        if not self.oqparam.imtls:
            raise ValueError('Missing intensity_measure_types!')
        self.precomputed_gmfs = False
