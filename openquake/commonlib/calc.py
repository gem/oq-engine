# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
import warnings
import logging
import numpy

from openquake.baselib import hdf5, parallel
from openquake.baselib.general import get_indices
from openquake.hazardlib.source import rupture
from openquake.hazardlib import calc, probability_map
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
    Given a set of hazard curve poes, interpolate a hazard map at the specified
    ``poe``.

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
    poes = numpy.array(poes)

    if len(poes.shape) == 0:
        # `poes` was passed in as a scalar;
        # convert it to 1D array of 1 element
        poes = poes.reshape(1)

    if len(curves.shape) == 1:
        # `curves` was passed as 1 dimensional array, there is a single site
        curves = curves.reshape((1,) + curves.shape)  # 1 x L

    L = curves.shape[1]  # number of levels
    if L != len(imls):
        raise ValueError('The curves have %d levels, %d were passed' %
                         (L, len(imls)))
    result = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # avoid RuntimeWarning: divide by zero encountered in log
        # happening in the classical_tiling tests
        imls = numpy.log(numpy.array(imls[::-1]))
    for curve in curves:
        # the hazard curve, having replaced the too small poes with EPSILON
        curve_cutoff = [max(poe, EPSILON) for poe in curve[::-1]]
        hmap_val = []
        for poe in poes:
            # special case when the interpolation poe is bigger than the
            # maximum, i.e the iml must be smaller than the minumum
            if poe > curve_cutoff[-1]:  # the greatest poes in the curve
                # extrapolate the iml to zero as per
                # https://bugs.launchpad.net/oq-engine/+bug/1292093
                # a consequence is that if all poes are zero any poe > 0
                # is big and the hmap goes automatically to zero
                hmap_val.append(0)
            else:
                # exp-log interpolation, to reduce numerical errors
                # see https://bugs.launchpad.net/oq-engine/+bug/1252770
                val = numpy.exp(
                    numpy.interp(
                        numpy.log(poe), numpy.log(curve_cutoff), imls))
                hmap_val.append(val)

        result.append(hmap_val)
    return numpy.array(result)


# #########################  GMF->curves #################################### #

# NB (MS): the approach used here will not work for non-poissonian models
def _gmvs_to_haz_curve(gmvs, imls, ses_per_logic_tree_path):
    """
    Given a set of ground motion values (``gmvs``) and intensity measure levels
    (``imls``), compute hazard curve probabilities of exceedance.

    :param gmvs:
        A list of ground motion values, as floats.
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
    num_exceeding = numpy.sum(numpy.array(gmvs) >= imls, axis=1)
    poes = 1 - numpy.exp(- num_exceeding / ses_per_logic_tree_path)
    return poes


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
        full_lt = dstore['full_lt']
        self.trt_by_grp = full_lt.trt_by_grp
        self.rlzs_by_gsim_grp = full_lt.get_rlzs_by_gsim_grp()
        self.samples_by_grp = full_lt.get_samples_by_grp()
        self.num_rlzs_by_grp = {
            grp_id:
            sum(len(rlzs) for rlzs in self.rlzs_by_gsim_grp[grp_id].values())
            for grp_id in self.rlzs_by_gsim_grp}

    def import_rups(self, rup_array):
        """
        Import an array of ruptures in the proper format
        """
        logging.info('Reordering the ruptures and storing the events')
        # order the ruptures by serial
        rup_array.sort(order='serial')
        nr = len(rup_array)
        assert len(numpy.unique(rup_array['serial'])) == nr  # sanity
        rup_array['geom_id'] = rup_array['id']
        rup_array['id'] = numpy.arange(nr)
        self.datastore['ruptures'] = rup_array
        self.save_events(rup_array)

    def save_events(self, rup_array):
        """
        :param rup_array: an array of ruptures with fields grp_id
        :returns: a list of RuptureGetters
        """
        from openquake.calculators.getters import RuptureGetter, gen_rgetters
        # this is very fast compared to saving the ruptures
        eids = rupture.get_eids(
            rup_array, self.samples_by_grp, self.num_rlzs_by_grp)
        self.check_overflow(len(eids))  # check the number of events
        events = numpy.zeros(len(eids), rupture.events_dt)
        # when computing the events all ruptures must be considered,
        # including the ones far away that will be discarded later on
        rgetters = gen_rgetters(self.datastore)
        # build the associations eid -> rlz sequentially or in parallel
        # this is very fast: I saw 30 million events associated in 1 minute!
        logging.info('Building assocs event_id -> rlz_id for {:_d} events'
                     ' and {:_d} ruptures'.format(len(events), len(rup_array)))
        if len(events) < 1E5:
            it = map(RuptureGetter.get_eid_rlz, rgetters)
        else:
            it = parallel.Starmap(RuptureGetter.get_eid_rlz,
                                  ((rgetter,) for rgetter in rgetters),
                                  progress=logging.debug,
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
