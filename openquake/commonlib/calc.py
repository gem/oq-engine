# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
"""
Here is an example of how to convert GMFs into mean hazard curves. Works
in the case of sampling, when the weights are all equal. It keeps
everything in memory and it is extremely fast.
NB: parallelization would kill the performance::

 def gmvs_to_mean_hcurves(dstore):
    # Convert GMFs into mean hazard curves. Works by keeping everything in
    # memory and it is extremely fast.
    # NB: parallelization would kill the performance.
    oq = dstore['oqparam']
    N = len(dstore['sitecol'])
    M = len(oq.imtls)
    L1 = oq.imtls.size // M
    gmf_df = dstore.read_df('gmf_data', 'sid')
    mean = numpy.zeros((N, 1, M, L1))
    for sid, df in gmf_df.groupby(gmf_df.index):
        gmvs = [df[col].to_numpy() for col in df.columns
                if col.startswith('gmv_')]
        mean[sid, 0] = calc.gmvs_to_poes(
            gmvs, oq.imtls, oq.ses_per_logic_tree_path)
    return mean
"""
import itertools
import warnings
import logging
from unittest.mock import Mock
import numpy

from openquake.baselib import parallel
from openquake.baselib.general import get_indices
from openquake.hazardlib.source import rupture
from openquake.hazardlib import probability_map
from openquake.hazardlib.source.rupture import EBRupture, events_dt
from openquake.commonlib import util

TWO16 = 2 ** 16
TWO32 = numpy.float64(2 ** 32)
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


# ######################### hazard maps ################################### #

# cutoff value for the poe
EPSILON = 1E-30


def compute_hazard_maps(curves, imls, poes):
    """
    Given a set of hazard curve poes, interpolate hazard maps at the specified
    ``poes``.

    :param curves:
        2D array of floats. Each row represents a curve, where the values
        in the row are the PoEs (Probabilities of Exceedance) corresponding to
        ``imls``. Each curve corresponds to a geographical location.
    :param imls:
        Intensity Measure Levels associated with these hazard ``curves``. Type
        should be an array-like of floats.
    :param poes:
        Value(s) on which to interpolate a hazard map from the input
        ``curves``. Can be an array-like or scalar value (for a single PoE).
    :returns:
        An array of shape N x P, where N is the number of curves and P the
        number of poes.
    """
    log_poes = numpy.log(poes)
    if len(log_poes.shape) == 0:
        # `poes` was passed in as a scalar;
        # convert it to 1D array of 1 element
        log_poes = log_poes.reshape(1)
    P = len(log_poes)

    if len(curves.shape) == 1:
        # `curves` was passed as 1 dimensional array, there is a single site
        curves = curves.reshape((1,) + curves.shape)  # 1 x L

    N, L = curves.shape  # number of levels
    if L != len(imls):
        raise ValueError('The curves have %d levels, %d were passed' %
                         (L, len(imls)))

    hmap = numpy.zeros((N, P))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # avoid RuntimeWarning: divide by zero for zero levels
        imls = numpy.log(numpy.array(imls[::-1]))
    for n, curve in enumerate(curves):
        # the hazard curve, having replaced the too small poes with EPSILON
        log_cutoff = numpy.log([max(poe, EPSILON) for poe in curve[::-1]])
        for p, log_poe in enumerate(log_poes):
            if log_poe > log_cutoff[-1]:
                # special case when the interpolation poe is bigger than the
                # maximum, i.e the iml must be smaller than the minumum
                # extrapolate the iml to zero as per
                # https://bugs.launchpad.net/oq-engine/+bug/1292093
                # a consequence is that if all poes are zero any poe > 0
                # is big and the hmap goes automatically to zero
                pass
            else:
                # exp-log interpolation, to reduce numerical errors
                # see https://bugs.launchpad.net/oq-engine/+bug/1252770
                hmap[n, p] = numpy.exp(numpy.interp(log_poe, log_cutoff, imls))
    return hmap


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

def make_hmap(pmap, imtls, poes, sid=None):
    """
    Compute the hazard maps associated to the passed probability map.

    :param pmap: hazard curves in the form of a ProbabilityMap
    :param imtls: DictArray with M intensity measure types
    :param poes: P PoEs where to compute the maps
    :param sid: not None when pmap is actually a ProbabilityCurve
    :returns: a ProbabilityMap with size (N, M, P)
    """
    if sid is None:
        sids = pmap.sids
    else:  # passed a probability curve
        pmap = {sid: pmap}
        sids = [sid]
    M, P = len(imtls), len(poes)
    hmap = probability_map.ProbabilityMap.build(M, P, sids, dtype=F32)
    if len(pmap) == 0:
        return hmap  # empty hazard map
    for i, imt in enumerate(imtls):
        curves = numpy.array([pmap[sid].array[imtls(imt), 0] for sid in sids])
        data = compute_hazard_maps(curves, imtls[imt], poes)  # array (N, P)
        for sid, value in zip(sids, data):
            array = hmap[sid].array
            for j, val in enumerate(value):
                array[i, j] = val
    return hmap


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
                uhs[str(poe)][imt] = hmap[:, m, p]
    return uhs


class RuptureImporter(object):
    """
    Import an array of ruptures correctly, i.e. by populating the datasets
    ruptures, rupgeoms, events.
    """
    def __init__(self, dstore):
        self.datastore = dstore
        self.oqparam = dstore['oqparam']

    def get_eid_rlz(self, proxies, rlzs_by_gsim):
        """
        :returns: a composite array with the associations eid->rlz
        """
        eid_rlz = []
        for rup in proxies:
            ebr = EBRupture(Mock(rup_id=rup['seed']), rup['source_id'],
                            rup['et_id'], rup['n_occ'], e0=rup['e0'])
            ebr.scenario = 'scenario' in self.oqparam.calculation_mode
            for rlz_id, eids in ebr.get_eids_by_rlz(rlzs_by_gsim).items():
                for eid in eids:
                    eid_rlz.append((eid, rup['id'], rlz_id))
        return numpy.array(eid_rlz, events_dt)

    def import_rups(self, rup_array):
        """
        Import an array of ruptures in the proper format
        """
        logging.info('Reordering the ruptures and storing the events')
        # order the ruptures by seed
        rup_array.sort(order='seed')
        nr = len(rup_array)
        seeds, counts = numpy.unique(rup_array['seed'], return_counts=True)
        if len(seeds) != nr:
            dupl = seeds[counts > 1]
            logging.info('The following %d rupture seeds are duplicated: %s',
                         len(dupl), dupl)
        rup_array['geom_id'] = rup_array['id']
        rup_array['id'] = numpy.arange(nr)
        self.datastore['ruptures'] = rup_array
        self.save_events(rup_array)

    def save_events(self, rup_array):
        """
        :param rup_array: an array of ruptures with fields et_id
        :returns: a list of RuptureGetters
        """
        from openquake.calculators.getters import gen_rupture_getters
        # this is very fast compared to saving the ruptures
        E = rup_array['n_occ'].sum()
        self.check_overflow(E)  # check the number of events
        events = numpy.zeros(E, rupture.events_dt)
        # when computing the events all ruptures must be considered,
        # including the ones far away that will be discarded later on
        rgetters = gen_rupture_getters(
            self.datastore, self.oqparam.concurrent_tasks)
        # build the associations eid -> rlz sequentially or in parallel
        # this is very fast: I saw 30 million events associated in 1 minute!
        logging.info('Associating event_id -> rlz_id for {:_d} events '
                     'and {:_d} ruptures'.format(len(events), len(rup_array)))
        iterargs = ((rg.proxies, rg.rlzs_by_gsim) for rg in rgetters)
        if len(events) < 1E5:
            it = itertools.starmap(self.get_eid_rlz, iterargs)
        else:
            it = parallel.Starmap(
                self.get_eid_rlz, iterargs, progress=logging.debug,
                h5=self.datastore.hdf5)
        i = 0
        for eid_rlz in it:
            for er in eid_rlz:
                events[i] = er
                i += 1
                if i >= TWO32:
                    raise ValueError('There are more than %d events!' % i)
        events.sort(order='rup_id')  # fast too
        # sanity check
        n_unique_events = len(numpy.unique(events[['id', 'rup_id']]))
        assert n_unique_events == len(events), (n_unique_events, len(events))
        events['id'] = numpy.arange(len(events))
        # set event year and event ses starting from 1
        nses = self.oqparam.ses_per_logic_tree_path
        extra = numpy.zeros(len(events), [('year', U32), ('ses_id', U32)])
        numpy.random.seed(self.oqparam.ses_seed)
        if self.oqparam.investigation_time:
            itime = int(self.oqparam.investigation_time)
            extra['year'] = numpy.random.choice(itime, len(events)) + 1
        extra['ses_id'] = numpy.random.choice(nses, len(events)) + 1
        self.datastore['events'] = util.compose_arrays(events, extra)
        eindices = get_indices(events['rup_id'])
        arr = numpy.array(list(eindices.values()))[:, 0, :]
        self.datastore['ruptures']['e0'] = arr[:, 0]
        self.datastore['ruptures']['e1'] = arr[:, 1]

    def check_overflow(self, E):
        """
        Raise a ValueError if the number of sites is larger than 65,536 or the
        number of IMTs is larger than 256 or the number of ruptures is larger
        than 4,294,967,296. The limits are due to the numpy dtype used to
        store the GMFs (gmv_dt). There also a limit of max_potential_gmfs on
        the number of sites times the number of events, to avoid producing too
        many GMFs. In that case split the calculation or be smarter.
        """
        oq = self.oqparam
        max_ = dict(sites=TWO32, events=TWO32, imts=2**8)
        num_ = dict(events=E, imts=len(self.oqparam.imtls))
        n = len(getattr(self, 'sitecol', ()) or ())
        num_['sites'] = n
        if oq.calculation_mode == 'event_based' and oq.ground_motion_fields:
            if n > oq.max_sites_per_gmf:
                raise ValueError(
                    'You cannot compute the GMFs for %d > %d sites' %
                    (n, oq.max_sites_per_gmf))
            elif n * E > oq.max_potential_gmfs:
                raise ValueError(
                    'A GMF calculation with %d sites and %d events is '
                    'impossibly large' % (n, E))
        for var in num_:
            if num_[var] > max_[var]:
                raise ValueError(
                    'The %s calculator is restricted to %d %s, got %d' %
                    (oq.calculation_mode, max_[var], var, num_[var]))
