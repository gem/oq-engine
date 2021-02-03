# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import (
    AccumDict, get_nbytes_msg, humansize, pprod, agg_probs,
    block_splitter, groupby)
from openquake.baselib.python3compat import encode
from openquake.hazardlib import stats
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.contexts import read_ctxs, RuptureContext
from openquake.hazardlib.tom import PoissonTOM
from openquake.commonlib import util, calc
from openquake.calculators import getters
from openquake.calculators import base

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


def _matrix(matrices, num_trts, num_mag_bins):
    # convert a dict trti, magi -> matrix into a single matrix
    trti, magi = next(iter(matrices))
    mat = numpy.zeros((num_trts, num_mag_bins) + matrices[trti, magi].shape)
    for trti, magi in matrices:
        mat[trti, magi] = matrices[trti, magi]
    return mat


def _hmap4(rlzs, iml_disagg, imtls, poes_disagg, curves):
    # an ArrayWrapper of shape (N, M, P, Z)
    N, Z = rlzs.shape
    P = len(poes_disagg)
    M = len(imtls)
    arr = numpy.empty((N, M, P, Z))
    for m, imt in enumerate(imtls):
        for (s, z), rlz in numpy.ndenumerate(rlzs):
            curve = curves[s][z]
            if poes_disagg == (None,):
                arr[s, m, 0, z] = imtls[imt]
            elif curve:
                rlz = rlzs[s, z]
                max_poe = curve[imt].max()
                arr[s, m, :, z] = calc.compute_hazard_maps(
                    curve[imt], imtls[imt], poes_disagg)
                for iml, poe in zip(arr[s, m, :, z], poes_disagg):
                    if iml == 0:
                        logging.warning('Cannot disaggregate for site %d, %s, '
                                        'poe=%s, rlz=%d: the hazard is zero',
                                        s, imt, poe, rlz)
                    elif poe > max_poe:
                        logging.warning(
                            POE_TOO_BIG, s, poe, max_poe, rlz, imt)
    return hdf5.ArrayWrapper(arr, {'rlzs': rlzs})


def output(mat6):
    """
    :param mat6: a 6D matrix with axis (D, Lo, La, E, P, Z)
    :returns: two matrices of shape (D, E, P, Z) and (Lo, La, P, Z)
    """
    return pprod(mat6, axis=(1, 2)), pprod(mat6, axis=(0, 3))


def compute_disagg(dstore, slc, cmaker, hmap4, trti, magi, bin_edges, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param dstore:
        a DataStore instance
    :param slc:
        a slice of ruptures
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param hmap4:
        an ArrayWrapper of shape (N, M, P, Z)
    :param trti:
        tectonic region type index
    :param magi:
        magnitude bin indices
    :param bin_egdes:
        a quartet (dist_edges, lon_edges, lat_edges, eps_edges)
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary sid, imti -> 6D-array
    """
    RuptureContext.temporal_occurrence_model = PoissonTOM(
        cmaker.investigation_time)
    with monitor('reading contexts', measuremem=True):
        dstore.open('r')
        allctxs, close_ctxs = read_ctxs(
            dstore, slc, req_site_params=cmaker.REQUIRES_SITES_PARAMETERS)
        for magidx, ctx in zip(magi, allctxs):
            ctx.magi = magidx
    dis_mon = monitor('disaggregate', measuremem=False)
    ms_mon = monitor('disagg mean_std', measuremem=True)
    N, M, P, Z = hmap4.shape
    g_by_z = AccumDict(accum={})  # dict s -> z -> g
    for g, rlzs in enumerate(cmaker.gsims.values()):
        for (s, z), r in numpy.ndenumerate(hmap4.rlzs):
            if r in rlzs:
                g_by_z[s][z] = g
    eps3 = disagg._eps3(cmaker.trunclevel, cmaker.num_epsilon_bins)
    imts = [from_string(im) for im in cmaker.imtls]
    for magi, ctxs in groupby(allctxs, operator.attrgetter('magi')).items():
        res = {'trti': trti, 'magi': magi}
        with ms_mon:
            # compute mean and std for a single IMT to save memory
            # the size is N * U * G * 16 bytes
            disagg.set_mean_std(ctxs, imts, cmaker.gsims)

        # disaggregate by site, IMT
        for s, iml3 in enumerate(hmap4):
            close = [ctx for ctx in close_ctxs[s] if ctx.magi == magi]
            if not g_by_z[s] or not close:
                # g_by_z[s] is empty in test case_7
                continue
            # dist_bins, lon_bins, lat_bins, eps_bins
            bins = (bin_edges[1], bin_edges[2][s], bin_edges[3][s],
                    bin_edges[4])
            iml2 = dict(zip(imts, iml3))
            with dis_mon:
                # 7D-matrix #distbins, #lonbins, #latbins, #epsbins, M, P, Z
                matrix = disagg.disaggregate(
                    close, g_by_z[s], iml2, eps3, s, bins)  # 7D-matrix
                for m in range(M):
                    mat6 = matrix[..., m, :, :]
                    if mat6.any():
                        res[s, m] = output(mat6)
        yield res
    # NB: compressing the results is not worth it since the aggregation of
    # the matrices is fast and the data are not queuing up


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

    def pre_checks(self):
        """
        Checks on the number of sites, atomic groups and size of the
        disaggregation matrix.
        """
        if self.N >= 32768:
            raise ValueError('You can disaggregate at max 32,768 sites')
        few = self.oqparam.max_sites_disagg
        if self.N > few:
            raise ValueError(
                'The number of sites is to disaggregate is %d, but you have '
                'max_sites_disagg=%d' % (self.N, few))
        if hasattr(self, 'csm'):
            for sg in self.csm.src_groups:
                if sg.atomic:
                    raise NotImplementedError(
                        'Atomic groups are not supported yet')
        elif self.datastore['source_info'].attrs['atomic']:
            raise NotImplementedError(
                'Atomic groups are not supported yet')
        all_edges, shapedic = disagg.get_edges_shapedic(
            self.oqparam, self.sitecol, self.datastore['source_mags'])
        *b, trts = all_edges
        T = len(trts)
        shape = [len(bin) - 1 for bin in
                 (b[0], b[1], b[2][0], b[3][0], b[4])] + [T]
        matrix_size = numpy.prod(shape)  # 6D
        if matrix_size > 1E6:
            raise ValueError(
                'The disaggregation matrix is too large '
                '(%d elements): fix the binning!' % matrix_size)
        tot = get_outputs_size(shapedic, self.oqparam.disagg_outputs)
        logging.info('Total output size: %s', humansize(sum(tot.values())))

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
        pcurves = self.pgetter.get_pcurves(sid)
        for z, rlz in enumerate(rlzs):
            pc = pcurves[rlz]
            if z == 0:
                self.curves.append(pc.array[:, 0])
            poes.append(pc.convert(self.oqparam.imtls))
        return poes

    def full_disaggregation(self):
        """
        Run the disaggregation phase.
        """
        oq = self.oqparam
        edges, self.shapedic = disagg.get_edges_shapedic(
            oq, self.sitecol, self.datastore['source_mags'])
        self.save_bin_edges(edges)
        self.full_lt = self.datastore['full_lt']
        self.poes_disagg = oq.poes_disagg or (None,)
        self.imts = list(oq.imtls)
        self.M = len(self.imts)
        ws = [rlz.weight for rlz in self.full_lt.get_realizations()]
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        self.pgetter = getters.PmapGetter(
            dstore, ws, self.sitecol.sids, oq.imtls, oq.poes)

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
                    # get the closest realization to the mean
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
        self.curves = []

        if oq.iml_disagg:
            # no hazard curves are needed
            self.poe_id = {None: 0}
            curves = [[None for z in range(Z)] for s in range(self.N)]
        else:
            self.poe_id = {poe: i for i, poe in enumerate(oq.poes_disagg)}
            curves = [self.get_curve(sid, rlzs[sid])
                      for sid in self.sitecol.sids]
        self.hmap4 = _hmap4(rlzs, oq.iml_disagg, oq.imtls,
                            self.poes_disagg, curves)
        if self.hmap4.array.sum() == 0:
            raise SystemExit('Cannot do any disaggregation: zero hazard')
        self.datastore['hmap4'] = self.hmap4
        self.datastore['poe4'] = numpy.zeros_like(self.hmap4.array)
        return self.compute()

    def compute(self):
        """
        Submit disaggregation tasks and return the results
        """
        oq = self.oqparam
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        magi = numpy.searchsorted(self.bin_edges[0], dstore['rup/mag'][:]) - 1
        magi[magi == -1] = 0  # when the magnitude is on the edge
        totrups = len(magi)
        logging.info('Reading {:_d} ruptures'.format(totrups))
        rdt = [('grp_id', U16), ('magi', U8), ('nsites', U16), ('idx', U32)]
        rdata = numpy.zeros(totrups, rdt)
        rdata['magi'] = magi
        rdata['idx'] = numpy.arange(totrups)
        rdata['grp_id'] = dstore['rup/grp_id'][:]
        rdata['nsites'] = dstore['rup/nsites'][:]
        totweight = rdata['nsites'].sum()
        et_ids = dstore['et_ids'][:]
        rlzs_by_gsim = self.full_lt.get_rlzs_by_gsim_list(et_ids)
        G = max(len(rbg) for rbg in rlzs_by_gsim)
        maxw = 2 * 1024**3 / (16 * G * self.M)  # at max 2 GB
        maxweight = min(
            numpy.ceil(totweight / (oq.concurrent_tasks or 1)), maxw)
        num_eff_rlzs = len(self.full_lt.sm_rlzs)
        task_inputs = []
        U = 0
        self.datastore.swmr_on()
        smap = parallel.Starmap(compute_disagg, h5=self.datastore.hdf5)
        # ABSURDLY IMPORTANT!! we rely on the fact that the classical part
        # of the calculation stores the ruptures in chunks of constant
        # grp_id, therefore it is possible to build (start, stop) slices;
        # we are NOT grouping by operator.itemgetter('grp_id', 'magi'):
        # that would break the ordering of the indices causing an incredibly
        # worse performance, but visible only in extra-large calculations!
        for block in block_splitter(rdata, maxweight,
                                    operator.itemgetter('nsites'),
                                    operator.itemgetter('grp_id')):
            grp_id = block[0]['grp_id']
            trti = et_ids[grp_id][0] // num_eff_rlzs
            trt = self.trts[trti]
            cmaker = ContextMaker(
                trt, rlzs_by_gsim[grp_id],
                {'truncation_level': oq.truncation_level,
                 'maximum_distance': oq.maximum_distance,
                 'collapse_level': oq.collapse_level,
                 'num_epsilon_bins': oq.num_epsilon_bins,
                 'investigation_time': oq.investigation_time,
                 'imtls': oq.imtls})
            U = max(U, block.weight)
            slc = slice(block[0]['idx'], block[-1]['idx'] + 1)
            smap.submit((dstore, slc, cmaker, self.hmap4, trti, magi[slc],
                         self.bin_edges))
            task_inputs.append((trti, slc.stop-slc.start))

        nbytes, msg = get_nbytes_msg(dict(M=self.M, G=G, U=U, F=2))
        logging.info('Maximum mean_std per task:\n%s', msg)

        s = self.shapedic
        Ta = numpy.ceil(len(task_inputs))
        nbytes = s['N'] * s['M'] * s['P'] * s['Z'] * Ta * 8
        data_transfer = (s['dist'] * s['eps'] + s['lon'] * s['lat']) * nbytes
        if data_transfer > oq.max_data_transfer:
            raise ValueError(
                'Estimated data transfer too big\n%s > max_data_transfer=%s' %
                (humansize(data_transfer), humansize(oq.max_data_transfer)))
        logging.info('Estimated data transfer: %s', humansize(data_transfer))

        dt = numpy.dtype([('trti', U8), ('nrups', U32)])
        self.datastore['disagg_task'] = numpy.array(task_inputs, dt)
        results = smap.reduce(self.agg_result, AccumDict(accum={}))
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
            for (s, m), out in result.items():
                for k in (0, 1):
                    x = acc[s, m, k].get((trti, magi), 0)
                    acc[s, m, k][trti, magi] = agg_probs(x, out[k])
        return acc

    def post_execute(self, results):
        """
        Save all the results of the disaggregation. NB: the number of results
        to save is #sites * #rlzs * #disagg_poes * #IMTs.

        :param results:
            a dictionary sid, imti, kind -> trti -> disagg matrix
        """
        # the DEBUG dictionary is populated only for OQ_DISTRIBUTE=no
        for sid, pnes in disagg.DEBUG.items():
            print('site %d, mean pnes=%s' % (sid, pnes))
        T = len(self.trts)
        Ma = len(self.bin_edges[0]) - 1  # num_mag_bins
        # build a dictionary s, m, k -> matrices
        results = {smk: _matrix(dic, T, Ma) for smk, dic in results.items()}
        # get the number of outputs
        shp = (self.N, len(self.poes_disagg), len(self.imts), self.Z)
        logging.info('Extracting and saving the PMFs for %d outputs '
                     '(N=%s, P=%d, M=%d, Z=%d)', numpy.prod(shp), *shp)
        with self.monitor('saving disagg results'):
            self.save_disagg_results(results)

    def save_bin_edges(self, all_edges):
        """
        Save disagg-bins
        """
        *self.bin_edges, self.trts = all_edges
        b = self.bin_edges

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

    def save_disagg_results(self, results):
        """
        Save the computed PMFs in the datastore

        :param results:
            a dict s, m, k -> 6D-matrix of shape (T, Ma, Lo, La, P, Z) or
            (T, Ma, D, E, P, Z) depending if k is 0 or k is 1
        """
        oq = self.oqparam
        out = output_dict(self.shapedic, oq.disagg_outputs)
        count = numpy.zeros(len(self.sitecol), U16)
        _disagg_trt = numpy.zeros(self.N, [(trt, float) for trt in self.trts])
        vcurves = []  # hazard curves with a vertical section for large poes
        for (s, m, k), mat6 in sorted(results.items()):
            imt = self.imts[m]
            for p, poe in enumerate(self.poes_disagg):
                mat5 = mat6[..., p, :]
                if k == 0 and m == 0 and poe == self.poes_disagg[-1]:
                    # mat5 has shape (T, Ma, D, E, Z)
                    _disagg_trt[s] = tuple(pprod(mat5[..., 0], axis=(1, 2, 3)))
                poe2 = pprod(mat5, axis=(0, 1, 2, 3))
                self.datastore['poe4'][s, m, p] = poe2  # shape Z
                poe_agg = poe2.mean()
                if (poe and abs(1 - poe_agg / poe) > .1 and not count[s]
                        and self.hmap4[s, m, p].any()):
                    logging.warning(
                        'Site #%d, IMT=%s: poe_agg=%s is quite different from '
                        'the expected poe=%s, perhaps not enough levels',
                        s, imt, poe_agg, poe)
                    vcurves.append(self.curves[s])
                    count[s] += 1
                mat4 = agg_probs(*mat5)  # shape (Ma D E Z) or (Ma Lo La Z)
                for key in oq.disagg_outputs:
                    if key == 'Mag' and k == 0:
                        out[key][s, m, p, :] = pprod(mat4, axis=(1, 2))
                    elif key == 'Dist' and k == 0:
                        out[key][s, m, p, :] = pprod(mat4, axis=(0, 2))
                    elif key == 'TRT' and k == 0:
                        out[key][s, m, p, :] = pprod(mat5, axis=(1, 2, 3))
                    elif key == 'Mag_Dist' and k == 0:
                        out[key][s, m, p, :] = pprod(mat4, axis=2)
                    elif key == 'Mag_Dist_Eps' and k == 0:
                        out[key][s, m, p, :] = mat4
                    elif key == 'Lon_Lat' and k == 1:
                        out[key][s, m, p, :] = pprod(mat4, axis=0)
                    elif key == 'Mag_Lon_Lat' and k == 1:
                        out[key][s, m, p, :] = mat4
                    elif key == 'Lon_Lat_TRT' and k == 1:
                        out[key][s, m, p, :] = pprod(mat5, axis=1).transpose(
                            1, 2, 0, 3)  # T Lo La Z -> Lo La T Z
                    # shape NMP..Z
        self.datastore['disagg'] = out
        # below a dataset useful for debugging, at minimum IMT and maximum RP
        self.datastore['_disagg_trt'] = _disagg_trt
        if len(vcurves):
            NML1 = len(vcurves), self.M, oq.imtls.size // self.M
            self.datastore['_vcurves'] = numpy.array(vcurves).reshape(NML1)
            self.datastore['_vcurves'].attrs['sids'] = numpy.where(count)[0]
