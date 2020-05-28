# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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
Disaggregation calculator core functionality
"""
import logging
import operator
import collections
import numpy
import pandas

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import (
    AccumDict, block_splitter, get_array_nbytes, humansize, pprod)
from openquake.baselib.python3compat import encode
from openquake.hazardlib import stats
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib.tom import PoissonTOM
from openquake.commonlib import util
from openquake.calculators import getters
from openquake.calculators import base

weight = operator.attrgetter('weight')
POE_TOO_BIG = '''\
Site #%d: you are trying to disaggregate for poe=%s.
However the source model produces at most probabilities
of %.7f for rlz=#%d, IMT=%s.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.'''
U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32


def _check_curves(sid, rlzs, curves, imtls, poes_disagg):
    # there may be sites where the sources are too small to produce
    # an effect at the given poes_disagg
    bad = 0
    for rlz, curve in zip(rlzs, curves):
        for imt in imtls:
            max_poe = curve[imt].max()
            for poe in poes_disagg:
                if poe > max_poe:
                    logging.warning(POE_TOO_BIG, sid, poe, max_poe, rlz, imt)
                    bad += 1
    return bool(bad)


def _matrix(matrices, num_trts, num_mag_bins):
    # convert a dict trti, magi -> matrix into a single matrix
    trti, magi = next(iter(matrices))
    mat = numpy.zeros((num_trts, num_mag_bins) + matrices[trti, magi].shape)
    for trti, magi in matrices:
        mat[trti, magi] = matrices[trti, magi]
    return mat


def _iml4(rlzs, iml_disagg, imtls, poes_disagg, curves):
    # a list of ArrayWrappers sid -> (M, P, Z)
    N, Z = rlzs.shape
    P = len(poes_disagg)
    M = len(imtls)
    imts = [from_string(imt) for imt in imtls]
    lst = [hdf5.ArrayWrapper(numpy.empty((M, P, Z)),
                             {'rlzs': rlzs[s], 'imts': imts})
           for s in range(N)]
    for m, imt in enumerate(imtls):
        for (s, z), rlz in numpy.ndenumerate(rlzs):
            curve = curves[s][z]
            if poes_disagg == (None,):
                lst[s][m, 0, z] = imtls[imt]
            elif curve:
                poes = curve[imt][::-1]
                imls = imtls[imt][::-1]
                lst[s][m, :, z] = numpy.interp(poes_disagg, poes, imls)
    return lst


def _prepare_ctxs(rupdata, sid, cmaker, sitecol, cfactors):
    # returns ctxs
    maxdist = cmaker.maximum_distance(cmaker.trt)
    ok, = numpy.where(rupdata['rrup_'][:, sid] <= maxdist)
    singlesite = sitecol.filtered([sid])
    ctxs = []
    for u in ok:  # consider only the ruptures close to the site
        ctx = RuptureContext()
        for par in rupdata:
            if not par.endswith('_'):
                setattr(ctx, par, rupdata[par][u])
            else:  # site-dependent parameter
                setattr(ctx, par[:-1], rupdata[par][u, [sid]])
        for par in cmaker.REQUIRES_SITES_PARAMETERS:
            setattr(ctx, par, singlesite[par])
        ctx.sids = singlesite.sids
        ctxs.append(ctx)
    if not ctxs:
        return []

    # collapse the contexts if the collapse_level is high enough
    if cmaker.collapse_level >= 2:
        ctxs_collapsed = cmaker.collapse_the_ctxs(ctxs)
        cfactors.append(len(ctxs_collapsed) / len(ctxs))
        ctxs = ctxs_collapsed
    else:
        cfactors.append(1.)
    return ctxs


def compute_disagg(dstore, idxs, cmaker, iml4, trti, magi, bin_edges, oq,
                   monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param dstore
        a DataStore instance
    :param idxs:
        an array of indices to ruptures
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param iml4:
        a list sid -> ArrayWrapper of shape (M, P, Z)
    :param trti:
        tectonic region type index
    :param magi:
        magnitude bin index
    :param bin_egdes:
        a quartet (dist_edges, lon_edges, lat_edges, eps_edges)
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary sid -> 7D-array
    """
    res = {'trti': trti, 'magi': magi}
    with monitor('reading rupdata', measuremem=True):
        dstore.open('r')
        sitecol = dstore['sitecol']
        # NB: using dstore['rup/' + k][idxs] would be ultraslow!
        a, b = idxs.min(), idxs.max() + 1
        rupdata = {k: dstore['rup/' + k][a:b][idxs-a] for k in dstore['rup']}
    RuptureContext.temporal_occurrence_model = PoissonTOM(
        oq.investigation_time)
    pne_mon = monitor('disaggregate_pne', measuremem=False)
    mat_mon = monitor('build_disagg_matrix', measuremem=False)
    ms_mon = monitor('disagg mean_std', measuremem=False)
    pre_mon = monitor('preparing contexts', measuremem=False)
    eps3 = disagg._eps3(cmaker.trunclevel, oq.num_epsilon_bins)
    cfactors = []
    for sid, iml3 in enumerate(iml4):
        with pre_mon:
            ctxs = _prepare_ctxs(rupdata, sid, cmaker, sitecol, cfactors)
        if not ctxs:
            continue

        # z indices by gsim
        M, P, Z = iml3.shape
        zs_by_gsim = AccumDict(accum=[])
        for gsim, rlzs in cmaker.gsims.items():
            for z in range(Z):
                if iml3.rlzs[z] in rlzs:
                    zs_by_gsim[gsim].append(z)

        # sanity check: the zs are disjoint
        counts = numpy.zeros(Z, numpy.uint8)
        for zs in zs_by_gsim.values():
            counts[zs] += 1
        assert (counts <= 1).all(), counts

        # dist_bins, lon_bins, lat_bins, eps_bins
        bins = bin_edges[0], bin_edges[1][sid], bin_edges[2][sid], bin_edges[3]
        # build 7D-matrix #distbins, #lonbins, #latbins, #epsbins, M, P, Z
        matrix = disagg.disaggregate(
            ctxs, iml3.imts, zs_by_gsim, iml3.array, eps3, bins,
            ms_mon, pne_mon, mat_mon)
        if matrix.any():
            res[sid] = matrix
    res['collapse_factor'] = numpy.mean(cfactors)
    return res


def agg_probs(*probs):
    """
    Aggregate probabilities with the usual formula 1 - (1 - P1) ... (1 - Pn)
    """
    acc = 1. - probs[0]
    for prob in probs[1:]:
        acc *= 1. - prob
    return 1. - acc


# the weight is the number of sites within 100 km from the rupture
RupIndex = collections.namedtuple('RupIndex', 'index weight')


def get_indices_by_gidx_mag(dstore, mag_edges):
    """
    :returns: a dictionary gidx, magi -> indices
    """
    acc = AccumDict(accum=[])  # gidx, magi -> indices
    close = dstore['rup/rrup_'][:] < 9999.  # close sites
    logging.info('Reading {:_d} ruptures'.format(len(close)))
    df = pandas.DataFrame(dict(gidx=dstore['rup/grp_id'][:],
                               mag=dstore['rup/mag'][:]))
    for (gidx, mag), d in df.groupby(['gidx', 'mag']):
        magi = numpy.searchsorted(mag_edges, mag) - 1
        for idx in d.index:
            weight = close[idx].sum()
            if weight:
                acc[gidx, magi].append(RupIndex(idx, weight))
    return acc


def get_outputs_size(shapedic, disagg_outputs):
    """
    :returns: the total size of the outputs
    """
    tot = AccumDict(accum=0)
    for out in disagg_outputs:
        tot[out] = 8
        for key in out.lower().split('_'):
            tot[out] *= shapedic[key]
    return tot * shapedic['N'] * shapedic['M'] * shapedic['P'] * shapedic['Z']


def output_dict(shapedic, disagg_outputs):
    N, M, P, Z = shapedic['N'], shapedic['M'], shapedic['P'], shapedic['Z']
    dic = {}
    for out in disagg_outputs:
        shp = tuple(shapedic[key] for key in out.lower().split('_'))
        dic[out] = numpy.zeros((N, M, P) + shp + (Z,))
    return dic


@base.calculators.add('disaggregation')
class DisaggregationCalculator(base.HazardCalculator):
    """
    Classical PSHA disaggregation calculator
    """
    precalc = 'classical'
    accept_precalc = ['classical', 'disaggregation']

    def init(self):
        if self.N >= 32768:
            raise ValueError('You can disaggregate at max 32,768 sites')
        few = self.oqparam.max_sites_disagg
        if self.N > few:
            raise ValueError(
                'The number of sites is to disaggregate is %d, but you have '
                'max_sites_disagg=%d' % (self.N, few))
        super().init()

    def execute(self):
        """Performs the disaggregation"""
        return self.full_disaggregation()

    def get_curve(self, sid, rlzs):
        """
        Get the hazard curves for the given site ID and realizations.

        :param sid: site ID
        :param rlzs: a matrix of indices of shape Z
        :returns: a list of Z arrays of PoEs
        """
        poes = []
        for rlz in rlzs:
            pmap = self.pgetter.get(rlz)
            poes.append(pmap[sid].convert(self.oqparam.imtls)
                        if sid in pmap else None)
        return poes

    def check_poes_disagg(self, curves, rlzs):
        """
        Raise an error if the given poes_disagg are too small compared to
        the hazard curves.
        """
        oq = self.oqparam
        # there may be sites where the sources are too small to produce
        # an effect at the given poes_disagg
        ok_sites = []
        for sid in self.sitecol.sids:
            if all(curve is None for curve in curves[sid]):
                ok_sites.append(sid)
                continue
            bad = _check_curves(sid, rlzs[sid], curves[sid],
                                oq.imtls, oq.poes_disagg)
            if not bad:
                ok_sites.append(sid)
        if len(ok_sites) == 0:
            raise SystemExit('Cannot do any disaggregation')
        elif len(ok_sites) < self.N:
            logging.warning('Doing the disaggregation on %s', self.sitecol)
        return ok_sites

    def full_disaggregation(self):
        """
        Run the disaggregation phase.
        """
        oq = self.oqparam
        mags_by_trt = self.datastore['source_mags']
        all_edges, self.shapedic = disagg.get_edges_shapedic(
            oq, self.sitecol, mags_by_trt)
        *self.bin_edges, self.trts = all_edges
        if hasattr(self, 'csm'):
            for sg in self.csm.src_groups:
                if sg.atomic:
                    raise NotImplementedError(
                        'Atomic groups are not supported yet')
        elif self.datastore['source_info'].attrs['atomic']:
            raise NotImplementedError(
                'Atomic groups are not supported yet')

        self.full_lt = self.datastore['full_lt']
        self.poes_disagg = oq.poes_disagg or (None,)
        self.imts = list(oq.imtls)
        self.M = len(self.imts)
        ws = [rlz.weight for rlz in self.full_lt.get_realizations()]
        self.pgetter = getters.PmapGetter(
            self.datastore, ws, self.sitecol.sids)

        # build array rlzs (N, Z)
        if oq.rlz_index is None:
            Z = oq.num_rlzs_disagg or 1
            rlzs = numpy.zeros((self.N, Z), int)
            if self.R > 1:
                for sid in self.sitecol.sids:
                    curves = numpy.array(
                        [pc.array for pc in self.pgetter.get_pcurves(sid)])
                    mean = getters.build_stat_curve(
                        curves, oq.imtls, stats.mean_curve, ws)
                    rlzs[sid] = util.closest_to_ref(curves, mean.array)[:Z]
            self.datastore['best_rlzs'] = rlzs
        else:
            Z = len(oq.rlz_index)
            rlzs = numpy.zeros((self.N, Z), int)
            for z in range(Z):
                rlzs[:, z] = oq.rlz_index[z]
            self.datastore['best_rlzs'] = rlzs
        assert Z <= self.R, (Z, self.R)
        self.Z = Z
        self.rlzs = rlzs

        if oq.iml_disagg:
            # no hazard curves are needed
            self.poe_id = {None: 0}
            curves = [[None for z in range(Z)] for s in range(self.N)]
            self.ok_sites = set(self.sitecol.sids)
        else:
            self.poe_id = {poe: i for i, poe in enumerate(oq.poes_disagg)}
            curves = [self.get_curve(sid, rlzs[sid])
                      for sid in self.sitecol.sids]
            self.ok_sites = set(self.check_poes_disagg(curves, rlzs))
        self.iml4 = _iml4(rlzs, oq.iml_disagg, oq.imtls,
                          self.poes_disagg, curves)
        iml4 = numpy.array(self.iml4)  # (N, M, P, Z)
        self.datastore['iml4/array'] = iml4
        self.datastore['iml4/rlzs'] = numpy.array(
            [iml3.rlzs for iml3 in self.iml4])  # shape (N, Z)
        self.datastore['poe4'] = numpy.zeros_like(iml4)

        self.save_bin_edges()
        tot = get_outputs_size(self.shapedic, oq.disagg_outputs)
        logging.info('Total output size: %s', humansize(sum(tot.values())))
        self.imldic = {}  # sid, rlz, poe, imt -> iml
        for s in self.sitecol.sids:
            iml3 = self.iml4[s]
            for z, rlz in enumerate(rlzs[s]):
                for p, poe in enumerate(self.poes_disagg):
                    for m, imt in enumerate(oq.imtls):
                        self.imldic[s, rlz, poe, imt] = iml3[m, p, z]

        # submit disaggregation tasks
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        mag_edges = self.bin_edges[0]
        indices = get_indices_by_gidx_mag(dstore, mag_edges)
        allargs = []
        totweight = sum(sum(ri.weight for ri in indices[gm])
                        for gm in indices)
        maxweight = int(numpy.ceil(totweight / (oq.concurrent_tasks or 1)))
        grp_ids = dstore['grp_ids'][:]
        rlzs_by_gsim = self.full_lt.get_rlzs_by_gsim_list(grp_ids)
        num_eff_rlzs = len(self.full_lt.sm_rlzs)
        task_inputs = []
        for gidx, magi in indices:
            trti = grp_ids[gidx][0] // num_eff_rlzs
            trt = self.trts[trti]
            cmaker = ContextMaker(
                trt, rlzs_by_gsim[gidx],
                {'truncation_level': oq.truncation_level,
                 'maximum_distance': oq.maximum_distance,
                 'collapse_level': oq.collapse_level,
                 'imtls': oq.imtls})
            for rupidxs in block_splitter(
                    indices[gidx, magi], maxweight, weight):
                idxs = numpy.array([ri.index for ri in rupidxs])
                allargs.append((dstore, idxs, cmaker, self.iml4,
                                trti, magi, self.bin_edges[1:], oq))
                task_inputs.append((trti, magi, len(idxs)))
        sd = self.shapedic.copy()
        sd.pop('trt')
        sd.pop('mag')
        sd['tasks'] = numpy.ceil(len(allargs))
        nbytes, msg = get_array_nbytes(sd)
        if nbytes > oq.max_data_transfer:
            raise ValueError(
                'Estimated data transfer too big\n%s > max_data_transfer=%s' %
                (msg, humansize(oq.max_data_transfer)))
        logging.info('Estimated data transfer:\n%s', msg)
        dt = numpy.dtype([('trti', U8), ('magi', U8), ('nrups', U32)])
        self.datastore['disagg_task'] = numpy.array(task_inputs, dt)
        self.datastore.swmr_on()
        self.collapse_factor = []
        smap = parallel.Starmap(
            compute_disagg, allargs, h5=self.datastore.hdf5)
        results = smap.reduce(self.agg_result, AccumDict(accum={}))
        cfactor = numpy.mean(self.collapse_factor)
        logging.info('Collapse factor=%.5f', cfactor)
        return results  # imti, sid -> trti, magi -> 6D array

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results.

        :param acc: dictionary sid -> trti, magi -> 6D array
        :param result: dictionary with the result coming from a task
        """
        # 7D array of shape (#distbins, #lonbins, #latbins, #epsbins, M, P, Z)
        with self.monitor('aggregating disagg matrices'):
            trti = result.pop('trti')
            magi = result.pop('magi')
            self.collapse_factor.append(result.pop('collapse_factor'))
            for sid, probs in result.items():
                before = acc[sid].get((trti, magi), 0)
                acc[sid][trti, magi] = agg_probs(before, probs)
        return acc

    def save_bin_edges(self):
        """
        Save disagg-bins
        """
        b = self.bin_edges
        T = len(self.trts)
        shape = [len(bin) - 1 for bin in
                 (b[0], b[1], b[2][0], b[3][0], b[4])] + [T]
        matrix_size = numpy.prod(shape)  # 6D
        if matrix_size > 1E6:
            raise ValueError(
                'The disaggregation matrix is too large '
                '(%d elements): fix the binning!' % matrix_size)

        def a(bin_no):
            # lon/lat edges for the sites, bin_no can be 2 or 3
            num_edges = len(b[bin_no][0])
            arr = numpy.zeros((self.N, num_edges))
            for sid, edges in b[bin_no].items():
                arr[sid] = edges
            return arr
        self.datastore['disagg-bins/Mag'] = b[0]
        self.datastore['disagg-bins/Dist'] = b[1]
        self.datastore['disagg-bins/Lon'] = a(2)
        self.datastore['disagg-bins/Lat'] = a(3)
        self.datastore['disagg-bins/Eps'] = b[4]
        self.datastore['disagg-bins/TRT'] = encode(self.trts)

    def post_execute(self, results):
        """
        Save all the results of the disaggregation. NB: the number of results
        to save is #sites * #rlzs * #disagg_poes * #IMTs.

        :param results:
            a dictionary sid -> trti -> disagg matrix
        """
        T = len(self.trts)
        Ma = len(self.bin_edges[0]) - 1  # num_mag_bins
        # build a dictionary s -> 9D matrix of shape (T, Ma, ..., E, M, P, Z)
        results = {s: _matrix(dic, T, Ma) for s, dic in results.items()}
        # get the number of outputs
        shp = (self.N, len(self.poes_disagg), len(self.imts), self.Z)
        logging.info('Extracting and saving the PMFs for %d outputs '
                     '(N=%s, P=%d, M=%d, Z=%d)', numpy.prod(shp), *shp)
        with self.monitor('saving disagg results'):
            odict = output_dict(self.shapedic, self.oqparam.disagg_outputs)
            self.save_disagg_results(results, odict)
            self.datastore['disagg'] = odict

    def save_disagg_results(self, results, out):
        """
        Save the computed PMFs in the datastore

        :param results:
            a dict s -> 9D-matrix of shape (T, Ma, D, Lo, La, E, M, P, Z)
        """
        outputs = self.oqparam.disagg_outputs
        for s, mat9 in results.items():
            if s not in self.ok_sites:
                continue
            for p, poe in enumerate(self.poes_disagg):
                mat8 = mat9[..., p, :]
                poe_agg = pprod(mat8, axis=(0, 1, 2, 3, 4, 5))
                self.datastore['poe4'][s, :, p] = poe_agg
                pa = poe_agg.mean()
                for m, imt in enumerate(self.imts):
                    mat7 = mat8[..., m, :]
                    mat6 = agg_probs(*mat7)  # 6D
                    for key in outputs:
                        pmf = disagg.pmf_map[key](
                            mat7 if key.endswith('TRT') else mat6)
                        out[key][:, m, p, :] = pmf
                    logging.warning(
                        'Site #%d: poe_agg=%s is quite different from the '
                        'expected poe=%s; perhaps the number of intensity '
                        'measure levels is too small?', s, pa, poe)
