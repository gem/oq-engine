# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
import operator
import functools
import numpy
from shapely.geometry import Point

from openquake.baselib import performance, parallel, hdf5, general
from openquake.hazardlib.source import rupture
from openquake.hazardlib import map_array, geo
from openquake.hazardlib.source.rupture import get_events
from openquake.commonlib import util, readinput, datastore

TWO16 = 2 ** 16
TWO24 = 2 ** 24
TWO30 = 2 ** 30
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
I64 = numpy.int64
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
    for sid, hcurve in pmap.items():
        curve = curves[sid]
        idx = 0
        for imt, imls in imtls.items():
            for iml in imls:
                curve['%s-%.3f' % (imt, iml)] = hcurve.array[idx, inner_idx]
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


# ################## utilities for event_based calculators ################ #

# TODO: see if it can be simplified
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
        hmap = map_array.MapArray(pmaps[0].sids, M, P).fill(0)
        for m, imt in enumerate(imtls):
            data = map_array.compute_hazard_maps(
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


def get_proxies(filename, rup_array, min_mag=0):
    """
    :returns: a list of RuptureProxies
    """
    proxies = []
    try:
        h5 = datastore.read(filename)
    except ValueError: # cannot extract calc_id
        h5 = hdf5.File(filename)
    with h5:
        rupgeoms = h5['rupgeoms']
        if hasattr(rup_array, 'start'):  # is a slice
            recs = h5['ruptures'][rup_array]
        else:
            recs = rup_array
        for rec in recs:
            proxy = rupture.RuptureProxy(rec)
            if proxy['mag'] < min_mag:
                # discard small magnitudes
                continue
            proxy.geom = rupgeoms[proxy['geom_id']]
            proxies.append(proxy)
    return proxies


class RuptureImporter(object):
    """
    Import an array of ruptures correctly, i.e. by populating the datasets
    ruptures, rupgeoms, events.
    """
    def __init__(self, dstore):
        self.datastore = dstore
        self.oqparam = dstore['oqparam']
        self.full_lt = dstore['full_lt']
        self.scenario = 'scenario' in self.oqparam.calculation_mode
        try:
            self.N = len(dstore['sitecol'])
        except KeyError:  # missing sitecol
            self.N = 0

    def get_eid_rlz(self, proxies, slc, rlzs_by_gsim, ordinal):
        """
        :returns: a composite array with the associations eid->rlz
        """
        rlzs = numpy.concatenate(list(rlzs_by_gsim.values()))
        return {ordinal: get_events(proxies, rlzs, self.scenario)}

    def import_rups_events(self, rup_array):
        """
        Import an array of ruptures and store the associated events.
        :returns: (number of imported ruptures, number of imported events)
        """
        oq = self.oqparam
        logging.info('Reordering the ruptures and storing the events')
        geom_id = numpy.argsort(rup_array[['trt_smr', 'id']])
        rup_array = rup_array[geom_id]
        self.datastore['rup_start_stop'] = performance.idx_start_stop(
            rup_array['trt_smr'])
        nr = len(rup_array)
        rupids = numpy.unique(rup_array['id'])
        assert len(rupids) == nr, 'rup_id not unique!'
        rup_array['geom_id'] = geom_id
        n_occ = rup_array['n_occ']        
        self.check_overflow(n_occ.sum())  # check the number of events
        rup_array['e0'][1:] = n_occ.cumsum()[:-1]
        idx_start_stop = performance.idx_start_stop(rup_array['trt_smr'])
        self.datastore.create_dset('trt_smr_start_stop', idx_start_stop)
        self._save_events(rup_array, idx_start_stop)
        if len(self.datastore['ruptures']):
            self.datastore['ruptures'].resize((0,))
        hdf5.extend(self.datastore['ruptures'], rup_array)
        nr, ne = len(rup_array), rup_array['n_occ'].sum()
        if oq.investigation_time:
            eff_time = (oq.investigation_time * oq.ses_per_logic_tree_path *
                        len(self.datastore['weights']))
            mag = numpy.average(rup_array['mag'], weights=rup_array['n_occ'])
            logging.info('There are {:_d} events and {:_d} ruptures in {:_d} '
                         'years (mean mag={:.2f})'.format(
                             ne, nr, int(eff_time), mag))

    def _save_events(self, rup_array, idx_start_stop):
        oq = self.oqparam
        # this is very fast compared to saving the ruptures
        E = rup_array['n_occ'].sum()
        events = numpy.zeros(E, rupture.events_dt)
        # DRAMATIC! the event IDs will be overridden a few lines below,
        # see the line events['id'] = numpy.arange(len(events))

        # when computing the events all ruptures must be considered,
        # including the ones far away that will be discarded later on
        # build the associations eid -> rlz sequentially or in parallel
        # this is very fast: I saw 30 million events associated in 1 minute!
        iterargs = []
        rlzs_by_gsim = self.full_lt.get_rlzs_by_gsim_dic()
        filename = self.datastore.filename
        for i, (trt_smr, start, stop) in enumerate(idx_start_stop):
            slc = slice(start, stop)
            proxies = get_proxies(filename, rup_array[slc])
            iterargs.append((proxies, slc, rlzs_by_gsim[trt_smr], i))
        acc = general.AccumDict()  # ordinal -> eid_rlz
        if len(events) < 1E5:
            for args in iterargs:
                acc += self.get_eid_rlz(*args)
        else:
            self.datastore.swmr_on()  # before the Starmap
            for res in parallel.Starmap(
                    self.get_eid_rlz, iterargs,
                    h5=self.datastore,
                    progress=logging.debug):
                acc += res
        i = 0
        for ordinal, eid_rlz in sorted(acc.items()):
            for er in eid_rlz:
                events[i] = er
                i += 1
                if i >= TWO32:
                    raise ValueError('There are more than %d events!' % i)

        # sanity check
        numpy.testing.assert_equal(events['id'], numpy.arange(E))

        # set event year and event ses starting from 1
        nses = oq.ses_per_logic_tree_path
        extra = numpy.zeros(len(events), [('year', U32), ('ses_id', U32)])

        rng = numpy.random.default_rng(oq.ses_seed)
        if oq.investigation_time:
            R = len(self.datastore['weights'])
            etime = int(oq.investigation_time * oq.ses_per_logic_tree_path)
            for r in range(R):
                ok, = numpy.where(events['rlz_id'] == r)
                extra['year'][ok] = rng.choice(etime, len(ok)) + r * etime + 1
        extra['ses_id'] = rng.choice(nses, len(events)) + 1
        self.datastore['events'] = util.compose_arrays(events, extra)

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


def _concat(acc, slc2):
    if len(acc) == 0:
        return [slc2]
    slc1 = acc[-1]  # last slice
    if slc2[0] == slc1[1]:
        new = numpy.array([slc1[0], slc2[1]])
        return acc[:-1] + [new]
    return acc + [slc2]


def compactify(arrayN2):
    """
    :param arrayN2: an array with columns (start, stop)
    :returns: a shorter array with the same structure

    Here is how it works in an example where the first three slices
    are compactified into one while the last slice stays as it is:

    >>> arr = numpy.array([[84384702, 84385520],
    ...                    [84385520, 84385770],
    ...                    [84385770, 84386062],
    ...                    [84387636, 84388028]])
    >>> compactify(arr)
    array([[84384702, 84386062],
           [84387636, 84388028]])
    """
    if len(arrayN2) == 1:
        # nothing to compactify
        return arrayN2
    out = numpy.array(functools.reduce(_concat, arrayN2, []))
    return out


# used in event_based_risk
def compactify3(arrayN3, maxsize=1_000_000):
    """
    :param arrayN3: an array with columns (idx, start, stop)
    :returns: a shorter array with columns (start, stop)
    """
    out = []
    for rows in general.block_splitter(
            arrayN3, maxsize, weight=lambda row: row[2]-row[1]):
        arr = numpy.vstack(rows)[:, 1:]
        out.append(compactify(arr))
    return numpy.concatenate(out)


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


def get_counts(idxs, N):
    """
    :param idxs: indices in the range 0..N-1
    :param N: size of the returned array
    :returns: an array of size N with the counts of the indices
    """
    counts = numpy.zeros(N, int)
    uni, cnt = numpy.unique(idxs, return_counts=True)
    counts[uni] = cnt
    return counts


def get_slices(sbe, data, num_assets):
    """
    :returns: a list of triple (start, stop, weight)
    """
    out = numpy.zeros(
        len(sbe), [('start', I64), ('stop', I64), ('weight', float)])
    start = sbe[0]['start']
    stop = sbe[-1]['stop']
    sids = data['sid'][start:stop]
    for i, rec in enumerate(sbe):
        s0, s1 = rec['start'], rec['stop']
        out[i]['start'] = s0
        out[i]['stop'] = s1
        out[i]['weight'] = num_assets[sids[s0-start:s1-start]].sum()
    return out


def starmap_from_gmfs(task_func, oq, dstore, mon):
    """
    :param task_func: function or generator with signature (gmf_df, oq, dstore)
    :param oq: an OqParam instance
    :param dstore: DataStore instance where the GMFs are stored
    :returns: a Starmap object used for event based calculations
    """
    data = dstore['gmf_data']
    if 'gmf_data' in dstore.parent:
        ds = dstore.parent
        gb = sum(data[k].nbytes for k in data) / 1024 ** 3
        logging.info('There are %.1f GB of GMFs', gb)
    else:
        ds = dstore
    try:
        N = len(ds['complete'])
    except KeyError:
        sitecol = ds['sitecol']
        # in ScenarioDamageTestCase.test_case_3 it is important to
        # consider sitecol.sids.max() + 1
        N = max(len(sitecol), sitecol.sids.max() + 1)
    with mon('computing event impact', measuremem=True):
        num_assets = get_counts(dstore['assetcol/array']['site_id'], N)
        try:
            sbe = data['slice_by_event'][:]
        except KeyError:
            eids = data['eid'][:]
            sbe = build_slice_by_event(eids)
            assert len(sbe) == len(numpy.unique(eids))  # sanity check
        slices = []
        logging.info('Reading event weights')
        for slc in general.gen_slices(0, len(sbe), 100_000):
            slices.append(get_slices(sbe[slc], data, num_assets))
        slices = numpy.concatenate(slices, dtype=slices[0].dtype)
    dstore.swmr_on()
    maxw = slices['weight'].sum() / (oq.concurrent_tasks or 1) or 1.
    logging.info('maxw = {:_d}'.format(int(maxw)))
    smap = parallel.Starmap.apply(
        task_func, (slices, oq, ds),
        # maxweight=200M is the limit to run Chile with 2 GB per core
        maxweight=min(maxw, 200_000_000),
        weight=operator.itemgetter('weight'),
        h5=dstore.hdf5)
    return smap


def get_close_mosaic_models(lon, lat, buffer_radius):
    """
    :param lon: longitude
    :param lat: latitude
    :param buffer_radius: radius of the buffer around the point.
        This distance is in the same units as the point's
        coordinates (i.e. degrees), and it defines how far from
        the point the buffer should extend in all directions,
        creating a circular buffer region around the point
    :returns: list of mosaic models intersecting the circle
        centered on the given coordinates having the specified radius
    """
    mosaic_df = readinput.read_mosaic_df(buffer=1)
    hypocenter = Point(lon, lat)
    hypo_buffer = hypocenter.buffer(buffer_radius)
    geoms = numpy.array([hypo_buffer])
    [close_mosaic_models] = geo.utils.geolocate_geometries(geoms, mosaic_df)
    if not close_mosaic_models:
        raise ValueError(
            f'({lon}, {lat}) is farther than {buffer_radius} deg'
            f' from any mosaic model!')
    elif len(close_mosaic_models) > 1:
        logging.info('(%s, %s) is close to the following mosaic models: %s',
                     lon, lat, close_mosaic_models)
    return close_mosaic_models
