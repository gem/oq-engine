# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
from unittest.mock import Mock
import numpy

from openquake.baselib import performance, parallel, hdf5, general
from openquake.hazardlib.source import rupture
from openquake.hazardlib import probability_map
from openquake.hazardlib.source.rupture import EBRupture, events_dt
from openquake.commonlib import util

TWO16 = 2 ** 16
TWO24 = 2 ** 24
TWO32 = numpy.float64(2 ** 32)
MAX_NBYTES = 1024**3
MAX_INT = 2 ** 31 - 1  # this is used in the random number generator
# in this way even on 32 bit machines Python will not have to convert
# the generated seed into a long integer

U8 = numpy.uint8
U16 = numpy.uint16
I32 = numpy.int32
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
F64 = numpy.float64

code2cls = rupture.BaseRupture.init()

# ############## utilities for the classical calculator ############### #


# used only in the view global_hcurves
def convert_to_array(pmap, nsites, imtls, inner_idx=0):
    """
    Convert the probability map into a composite array with header
    of the form PGA-0.1, PGA-0.2 ...

    :param pmap: probability map
    :param nsites: total number of sites
    :param imtls: a DictArray with IMT and levels
    :returns: a composite array of lenght nsites
    """
    lst = []
    # build the export dtype, of the form PGA-0.1, PGA-0.2 ...
    for imt, imls in imtls.items():
        for iml in imls:
            lst.append(('%s-%.3f' % (imt, iml), F32))
    curves = numpy.zeros(nsites, numpy.dtype(lst))
    for sid, pcurve in pmap.items():
        curve = curves[sid]
        idx = 0
        for imt, imls in imtls.items():
            for iml in imls:
                curve['%s-%.3f' % (imt, iml)] = pcurve.array[idx, inner_idx]
                idx += 1
    return curves


# #########################  GMF->curves #################################### #

# NB (MS): the approach used here will not work for non-poissonian models
def _gmvs_to_haz_curve(gmvs, imls, ses_per_logic_tree_path):
    """
    Given a set of ground motion values (``gmvs``) and intensity measure levels
    (``imls``), compute hazard curve probabilities of exceedance.

    :param gmvs:
        Am array of ground motion values, as floats.
    :param imls:
        A list of intensity measure levels, as floats.
    :param ses_per_logic_tree_path:
        Number of stochastic event sets: the larger, the best convergency

    :returns:
        Numpy array of PoEs (probabilities of exceedance).
    """
    # convert to numpy array and redimension so that it can be broadcast with
    # the gmvs for computing PoE values; there is a gmv for each rupture
    # here is an example: imls = [0.03, 0.04, 0.05], gmvs=[0.04750576]
    # => num_exceeding = [1, 1, 0] coming from 0.04750576 > [0.03, 0.04, 0.05]
    imls = numpy.array(imls).reshape((len(imls), 1))
    num_exceeding = numpy.sum(gmvs >= imls, axis=1)
    poes = 1 - numpy.exp(- num_exceeding / ses_per_logic_tree_path)
    return poes


def gmvs_to_poes(df, imtls, ses_per_logic_tree_path):
    """
    :param df: a DataFrame with fields gmv_0, .. gmv_{M-1}
    :param imtls: a dictionary imt -> imls with M IMTs and L levels
    :param ses_per_logic_tree_path: a positive integer
    :returns: an array of PoEs of shape (M, L)
    """
    M = len(imtls)
    L = len(imtls[next(iter(imtls))])
    arr = numpy.zeros((M, L))
    for m, imt in enumerate(imtls):
        arr[m] = _gmvs_to_haz_curve(
            df[f'gmv_{m}'].to_numpy(), imtls[imt], ses_per_logic_tree_path)
    return arr


# ################## utilities for classical calculators ################ #

# TODO: see if it can be simplified, in terms of compute_hmap4
def make_hmaps(pmaps, imtls, poes):
    """
    Compute the hazard maps associated to the passed probability maps.

    :param pmaps: a list of Pmaps of shape (N, M, L1)
    :param imtls: DictArray with M intensity measure types
    :param poes: P PoEs where to compute the maps
    :returns: a list of Pmaps with size (N, M, P)
    """
    M, P = len(imtls), len(poes)
    hmaps = []
    for pmap in pmaps:
        hmap = probability_map.ProbabilityMap(pmaps[0].sids, M, P).fill(0)
        for m, imt in enumerate(imtls):
            data = probability_map.compute_hazard_maps(
                pmap.array[:, m], imtls[imt], poes)  # (N, P)
            for idx, imls in enumerate(data):
                for p, iml in enumerate(imls):
                    hmap.array[idx, m, p] = iml
        hmaps.append(hmap)
    return hmaps


def make_uhs(hmap, info):
    """
    Make Uniform Hazard Spectra curves for each location.

    :param hmap:
        array of shape (N, M, P)
    :param info:
        a dictionary with keys poes, imtls, uhs_dt
    :returns:
        a composite array containing uniform hazard spectra
    """
    uhs = numpy.zeros(len(hmap), info['uhs_dt'])
    for p, poe in enumerate(info['poes']):
        for m, imt in enumerate(info['imtls']):
            if imt.startswith(('PGA', 'SA')):
                uhs['%.6f' % poe][imt] = hmap[:, m, p]
    return uhs


class RuptureImporter(object):
    """
    Import an array of ruptures correctly, i.e. by populating the datasets
    ruptures, rupgeoms, events.
    """
    def __init__(self, dstore):
        self.datastore = dstore
        self.oqparam = dstore['oqparam']
        try:
            self.N = len(dstore['sitecol'])
        except KeyError:  # missing sitecol
            self.N = 0

    def get_eid_rlz(self, proxies, rlzs_by_gsim, ordinal):
        """
        :returns: a composite array with the associations eid->rlz
        """
        eid_rlz = []
        for rup in proxies:
            srcid, rupid = divmod(int(rup['id']), TWO24)
            ebr = EBRupture(
                Mock(), rup['source_id'],
                rup['trt_smr'], rup['n_occ'], rupid, e0=rup['e0'],
                scenario='scenario' in self.oqparam.calculation_mode)
            ebr.seed = rup['seed']
            for rlz_id, eids in ebr.get_eids_by_rlz(rlzs_by_gsim).items():
                for eid in eids:
                    eid_rlz.append((eid, rup['id'], rlz_id))
        return {ordinal: numpy.array(eid_rlz, events_dt)}

    def import_rups_events(self, rup_array, get_rupture_getters):
        """
        Import an array of ruptures and store the associated events.
        :returns: (number of imported ruptures, number of imported events)
        """
        oq = self.oqparam
        logging.info('Reordering the ruptures and storing the events')
        geom_id = numpy.argsort(rup_array['seed'])
        rup_array = rup_array[geom_id]
        nr = len(rup_array)
        rupids = numpy.unique(rup_array['id'])
        assert len(rupids) == nr, 'rup_id not unique!'
        rup_array['geom_id'] = geom_id
        if len(self.datastore['ruptures']):
            self.datastore['ruptures'].resize((0,))
        hdf5.extend(self.datastore['ruptures'], rup_array)
        rgetters = get_rupture_getters(  # fast
            self.datastore, self.oqparam.concurrent_tasks)
        self._save_events(rup_array, rgetters)
        nr, ne = len(rup_array), rup_array['n_occ'].sum()
        if oq.investigation_time:
            eff_time = (oq.investigation_time * oq.ses_per_logic_tree_path *
                        len(self.datastore['weights']))
            mag = numpy.average(rup_array['mag'], weights=rup_array['n_occ'])
            logging.info('There are {:_d} events and {:_d} ruptures in {:_d} '
                         'years (mean mag={:.2f})'.format(
                             ne, nr, int(eff_time), mag))

    def _save_events(self, rup_array, rgetters):
        # this is very fast compared to saving the ruptures
        E = rup_array['n_occ'].sum()
        self.check_overflow(E)  # check the number of events
        events = numpy.zeros(E, rupture.events_dt)
        # DRAMATIC! the event IDs will be overridden a few lines below,
        # see the line events['id'] = numpy.arange(len(events))

        # when computing the events all ruptures must be considered,
        # including the ones far away that will be discarded later on
        # build the associations eid -> rlz sequentially or in parallel
        # this is very fast: I saw 30 million events associated in 1 minute!
        iterargs = []
        for i, rg in enumerate(rgetters):
            iterargs.append((rg.proxies, rg.rlzs_by_gsim, i))
        if len(events) < 1E5:
            acc = general.AccumDict()  # ordinal -> eid_rlz
            for args in iterargs:
                acc += self.get_eid_rlz(*args)
        else:
            acc = parallel.Starmap(
                self.get_eid_rlz, iterargs, progress=logging.debug).reduce()
        i = 0
        for ordinal, eid_rlz in sorted(acc.items()):
            for er in eid_rlz:
                events[i] = er
                i += 1
                if i >= TWO32:
                    raise ValueError('There are more than %d events!' % i)

        # sanity check
        n_unique_events = len(numpy.unique(events[['id', 'rup_id']]))
        assert n_unique_events == len(events), (n_unique_events, len(events))
        events['id'] = numpy.arange(len(events))
        # set event year and event ses starting from 1
        nses = self.oqparam.ses_per_logic_tree_path
        extra = numpy.zeros(len(events), [('year', U32), ('ses_id', U32)])

        # TODO: use default_rng here
        numpy.random.seed(self.oqparam.ses_seed)
        if self.oqparam.investigation_time:
            itime = int(self.oqparam.investigation_time)
            extra['year'] = numpy.random.choice(itime, len(events)) + 1
        extra['ses_id'] = numpy.random.choice(nses, len(events)) + 1
        self.datastore['events'] = util.compose_arrays(events, extra)
        cumsum = self.datastore['ruptures']['n_occ'].cumsum()
        rup_array['e0'][1:] = cumsum[:-1]
        self.datastore['ruptures']['e0'] = rup_array['e0']

    def check_overflow(self, E):
        """
        Raise a ValueError if the number of IMTs is larger than 256 or the
        number of events is larger than 4,294,967,296. The limits
        are due to the numpy dtype used to store the GMFs
        (gmv_dt). There also a limit of `max_potential_gmfs` on the
        number of sites times the number of events, to avoid producing
        too many GMFs. In that case split the calculation or be
        smarter.
        """
        oq = self.oqparam
        if len(oq.imtls) > 256:
            raise ValueError('The event_based calculator is restricted '
                             'to 256 imts, got %d' % len(oq.imtls))
        if E > TWO32:
            raise ValueError('The event_based calculator is restricted '
                             'to 2^32 events, got %d' % E)
        max_ = dict(sites=TWO32, events=TWO32, imts=2**8)
        num_ = dict(events=E, imts=len(self.oqparam.imtls))
        num_['sites'] = self.N
        if oq.calculation_mode == 'event_based' and oq.ground_motion_fields:
            if self.N * E > oq.max_potential_gmfs:
                raise ValueError(
                    'A GMF calculation with {:_d} sites and {:_d} events is '
                    'forbidden unless you raise `max_potential_gmfs` to {:_d}'.
                    format(self.N, int(E), int(self.N * E)))
        for var in num_:
            if num_[var] > max_[var]:
                raise ValueError(
                    'The %s calculator is restricted to %d %s, got %d' %
                    (oq.calculation_mode, max_[var], var, num_[var]))


##############################################################
# logic for building the GMF slices used in event_based_risk #
##############################################################

SLICE_BY_EVENT_NSITES = 1000

slice_dt = numpy.dtype([('start', int), ('stop', int), ('eid', U32)])


def build_slice_by_event(eids, offset=0):
    arr = performance.idx_start_stop(eids)
    sbe = numpy.zeros(len(arr), slice_dt)
    sbe['eid'] = arr[:, 0]
    sbe['start'] = arr[:, 1] + offset
    sbe['stop'] = arr[:, 2] + offset
    return sbe


def starmap_from_gmfs(task_func, oq, dstore):
    """
    :param task_func: function or generator with signature (gmf_df, oq, dstore)
    :param oq: an OqParam instance
    :param dstore: DataStore instance where the GMFs are stored
    :returns: a Starmap object used for event based calculations
    """
    data = dstore['gmf_data']
    try:
        sbe = data['slice_by_event'][:]
    except KeyError:
        sbe = build_slice_by_event(data['eid'][:])
    nrows = sbe[-1]['stop'] - sbe[0]['start']
    maxweight = numpy.ceil(nrows / (oq.concurrent_tasks or 1))
    dstore.swmr_on()  # before the Starmap
    smap = parallel.Starmap.apply(
        task_func, (sbe, oq, dstore),
        weight=lambda rec: rec['stop']-rec['start'],
        maxweight=numpy.clip(maxweight, 1000, 10_000_000),
        h5=dstore.hdf5)
    return smap
