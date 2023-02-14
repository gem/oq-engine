# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
import numpy

from openquake.baselib import parallel, hdf5, performance
from openquake.baselib.general import (
    AccumDict, get_nbytes_msg, humansize, pprod, agg_probs, gen_slices)
from openquake.baselib.python3compat import encode
from openquake.hazardlib import stats
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.contexts import read_cmakers, FarAwayRupture
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


def _collapse_res(rdic):
    # reduce the result dictionary for debugging purposes
    # s, m -> (array, array)
    cdic = {}
    for tup, out in rdic.items():
        if isinstance(tup, tuple):
            cdic[tup] = pprod(out[0])
    return cdic


def matrix_dict(acc, num_trts, num_mag_bins):
    # # build a dictionary s, r, m, k -> matrix from a double dictionary
    # s, r, m -> trti, magi -> output
    out = {}
    for s, r, m in acc:
        output = acc[s, r, m]  # dictionary (trti, magi) -> output
        trti, magi = next(iter(output))
        for k in (0, 1):
            shp = (num_trts, num_mag_bins) + output[trti, magi][k].shape
            mat = numpy.zeros(shp)
            for trti, magi in output:
                mat[trti, magi] = output[trti, magi][k]
            out[s, r, m, k] = mat
    return out


def _iml4(rlzs, iml_disagg, imtls, poes_disagg, curves):
    # an ArrayWrapper of shape (N, M, P, Z)
    N, Z = rlzs.shape
    P = len(poes_disagg)
    M = len(imtls)
    arr = numpy.empty((N, M, P, Z))
    acc = AccumDict(accum=[])  # site, imt, poe -> rlzs
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
                        acc[s, imt, poe].append(rlz)
                    elif poe > max_poe:
                        logging.warning(
                            POE_TOO_BIG, s, poe, max_poe, rlz, imt)
    for (s, imt, poe), zero_rlzs in acc.items():
        logging.warning('Cannot disaggregate for site %d, %s, '
                        'poe=%s, rlzs=%s: the hazard is zero',
                        s, imt, poe, zero_rlzs)
    return hdf5.ArrayWrapper(arr, {'rlzs': rlzs})


def output(mat5):
    """
    :param mat5: a 5D matrix with axis (D, Lo, La, E, P)
    :returns: two matrices of shape (D, E, P) and (Lo, La, P)
    """
    return pprod(mat5, axis=(1, 2)), pprod(mat5, axis=(0, 3))


def compute_disagg(dis, triples, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param dis:
        a Disaggregator instance
    :param triples:
        a list of triples (g, rlz, iml2)
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary s, z, m -> (arr[D, E, P, Z], arr[Lo, La, P, Z])
    """
    with monitor('building mean_std', measuremem=False):
        dis.init(monitor)
    [magi] = dis.ctxs
    res = {'trti': dis.cmaker.trti, 'magi': magi}
    for g, rlz, iml2 in triples:
        mat6 = dis.disagg6D(iml2, g, magi)
        for m in range(len(iml2)):
            mat5 = mat6[..., m, :]
            if mat5.any():
                res[dis.sid, rlz, m] = output(mat5)
        # print(_collapse_res(res))
    return res
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
        self.oqparam.mags_by_trt = self.datastore['source_mags']
        all_edges, shapedic = disagg.get_edges_shapedic(
            self.oqparam, self.sitecol, self.R)
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
        pcurve = self.pgetter.get_pcurve(sid)
        for z, rlz in enumerate(rlzs):
            pc = pcurve.extract(rlz)
            if z == 0:
                self.curves.append(pc.array[:, 0])
            poes.append(pc.convert(self.oqparam.imtls))
        return poes

    def full_disaggregation(self):
        """
        Run the disaggregation phase.
        """
        oq = self.oqparam
        try:
            full_lt = self.full_lt
        except AttributeError:
            full_lt = self.datastore['full_lt']
        ws = [rlz.weight for rlz in full_lt.get_realizations()]
        if oq.rlz_index is None and oq.num_rlzs_disagg == 0:
            oq.num_rlzs_disagg = len(ws)  # 0 means all rlzs
        self.oqparam.mags_by_trt = self.datastore['source_mags']
        edges, self.shapedic = disagg.get_edges_shapedic(
            oq, self.sitecol, self.R)
        logging.info(self.shapedic)
        self.save_bin_edges(edges)
        self.full_lt = self.datastore['full_lt']
        self.poes_disagg = oq.poes_disagg or (None,)
        self.imts = list(oq.imtls)
        self.M = len(self.imts)
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        nrows = len(dstore['_poes/sid'])
        self.pgetter = getters.PmapGetter(
            dstore, ws, [(0, nrows + 1)], oq.imtls, oq.poes)

        # build array rlzs (N, Z)
        if oq.rlz_index is None:
            Z = oq.num_rlzs_disagg
            rlzs = numpy.zeros((self.N, Z), int)
            if self.R > 1:
                for sid in self.sitecol.sids:
                    pcurve = self.pgetter.get_pcurve(sid)
                    mean = getters.build_stat_curve(
                        pcurve, oq.imtls, stats.mean_curve, ws)
                    # get the closest realization to the mean
                    rlzs[sid] = util.closest_to_ref(
                        pcurve.array.T, mean.array)[:Z]
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
        self.iml4 = _iml4(rlzs, oq.iml_disagg, oq.imtls,
                            self.poes_disagg, curves)
        if self.iml4.array.sum() == 0:
            raise SystemExit('Cannot do any disaggregation: zero hazard')
        self.datastore['hmap4'] = self.iml4
        self.datastore['poe4'] = numpy.zeros_like(self.iml4.array)
        self.sr2z = {(s, r): z for s in self.sitecol.sids
                     for z, r in enumerate(rlzs[s])}
        return self.compute()

    def compute(self):
        """
        Submit disaggregation tasks and return the results
        """
        oq = self.oqparam
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        totrups = len(dstore['rup/mag'])
        logging.info('Reading {:_d} ruptures'.format(totrups))
        rdt = [('grp_id', U16), ('magi', U8), ('nsites', U16), ('idx', U32)]
        rdata = numpy.zeros(totrups, rdt)
        rdata['idx'] = numpy.arange(totrups)
        rdata['grp_id'] = dstore['rup/grp_id'][:]
        task_inputs = []
        U = 0
        self.datastore.swmr_on()
        smap = parallel.Starmap(compute_disagg, h5=self.datastore.hdf5)
        # IMPORTANT!! we rely on the fact that the classical part
        # of the calculation stores the ruptures in chunks of constant
        # grp_id, therefore it is possible to build (start, stop) slices;
        # we are NOT grouping by operator.itemgetter('grp_id', 'magi'):
        # that would break the ordering of the indices causing an incredibly
        # worse performance, but visible only in extra-large calculations!
        cmakers = read_cmakers(self.datastore)
        grp_ids = rdata['grp_id']
        G = max(len(cmaker.gsims) for cmaker in cmakers)
        s = self.shapedic
        nbytes = 0
        for grp_id, slices in performance.get_slices(grp_ids).items():
            cmaker = cmakers[grp_id]
            for start, stop in slices:
                ctxs = cmaker.read_ctxs(self.datastore, slice(start, stop))
                if cmaker.rup_mutex:
                    raise NotImplementedError(
                        'Disaggregation with mutex ruptures')
                for site in self.sitecol:
                    sid = site.id
                    try:
                        dgator = disagg.Disaggregator(
                            ctxs, site, cmaker, self.bin_edges)
                    except FarAwayRupture:  # no data for this site
                        continue
                    iml3 = self.iml4[sid]
                    triples = []
                    for z, rlz in enumerate(self.iml4.rlzs[sid]):
                        try:
                            g = dgator.g_by_rlz[rlz]
                        except KeyError:
                            continue
                        iml2 = iml3[:, :, z]
                        if iml2.any():
                            triples.append((g, rlz, iml2))
                    nonzero = (iml3 > 0).sum()
                    nbytes += nonzero * 8
                    if nonzero == 0:  # nothing to disaggregate
                        continue
                    del dgator.g_by_rlz  # save data transfer
                    for magi, dis in dgator.split_by_magi():
                        n = sum(len(ctx) for ctx in dis.ctxs[magi])
                        U = max(U, n)
                        smap.submit((dis, triples))
                        task_inputs.append((grp_id, n))

        nbytes, msg = get_nbytes_msg(dict(M=self.M, G=G, U=U, F=2))
        logging.info('Maximum mean_std per task:\n%s', msg)

        data_transfer = (s['dist'] * s['eps'] + s['lon'] * s['lat']) * nbytes
        if data_transfer > oq.max_data_transfer:
            raise ValueError(
                'Estimated data transfer too big\n%s > max_data_transfer=%s' %
                (humansize(data_transfer), humansize(oq.max_data_transfer)))
        logging.info('Estimated data transfer: %s', humansize(data_transfer))

        dt = numpy.dtype([('grp_id', U8), ('nrups', U32)])
        self.datastore['disagg_task'] = numpy.array(task_inputs, dt)
        DEP = numpy.zeros((s['dist'], s['eps'], s['P']))
        LLP = numpy.zeros((s['lon'], s['lat'], s['P']))
        acc = AccumDict(accum=AccumDict(accum=(DEP, LLP)))
        results = smap.reduce(self.agg_result, acc)
        return results  # s, m -> trti, magi -> output

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results.

        :param acc: dictionary sid -> trti, magi -> output
        :param result: dictionary with the result coming from a task
        """
        with self.monitor('aggregating disagg matrices'):
            trti = result.pop('trti')
            magi = result.pop('magi')
            for (s, r, m), out in result.items():
                for k in (0, 1):
                    accum = acc[s, r, m][trti, magi][k]
                    accum[:] = agg_probs(accum[:], out[k])
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
        results = matrix_dict(results, T, Ma)
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

        def ll_edges(bin_no):
            # lon/lat edges for the sites, bin_no can be 2 or 3
            num_edges = len(b[bin_no][0])
            arr = numpy.zeros((self.N, num_edges))
            for sid, edges in b[bin_no].items():
                arr[sid] = edges
            return arr
        self.datastore['disagg-bins/Mag'] = b[0]
        self.datastore['disagg-bins/Dist'] = b[1]
        self.datastore['disagg-bins/Lon'] = ll_edges(2)
        self.datastore['disagg-bins/Lat'] = ll_edges(3)
        self.datastore['disagg-bins/Eps'] = b[4]
        self.datastore['disagg-bins/TRT'] = encode(self.trts)

    def save_disagg_results(self, results):
        """
        Save the computed PMFs in the datastore

        :param results:
            a dict s, r, m, k -> 5D-matrix of shape (T, Ma, Lo, La, P) or
            (T, Ma, D, E, P) depending if k is 0 or k is 1
        """
        oq = self.oqparam
        out = output_dict(self.shapedic, oq.disagg_outputs)
        count = numpy.zeros(len(self.sitecol), U16)
        _disagg_trt = numpy.zeros(self.N, [(trt, float) for trt in self.trts])
        vcurves = []  # hazard curves with a vertical section for large poes
        for (s, r, m, k), mat5 in sorted(results.items()):
            z = self.sr2z[s, r]
            # NB: k is an index with value 0 (MagDistEps) or 1 (LonLat)
            imt = self.imts[m]
            for p, poe in enumerate(self.poes_disagg):
                mat4 = mat5[..., p]
                # mat3 has shape (T, Ma, D, E) for k == 0
                # and (T, Ma, Lo, La) for k == 1
                if k == 0 and m == 0 and poe == self.poes_disagg[-1]:
                    _disagg_trt[s] = tuple(pprod(mat5[..., 0], axis=(1, 2, 3)))
                poe = pprod(mat4, axis=(0, 1, 2, 3))
                self.datastore['poe4'][s, m, p, z] = poe
                '''
                if (poe and abs(1 - poe_agg / poe) > .1 and not count[s]
                        and self.iml4[s, m, p].any()):
                    logging.warning(
                        'Site #%d, IMT=%s: poe_agg=%s is quite different from '
                        'the expected poe=%s, perhaps not enough levels',
                        s, imt, poe_agg, poe)
                    vcurves.append(self.curves[s])
                    count[s] += 1
                '''
                mat3 = agg_probs(*mat4)  # shape (Ma D E) or (Ma Lo La)
                for key in oq.disagg_outputs:
                    if key == 'Mag' and k == 0:
                        out[key][s, m, p, :, z] = pprod(mat3, axis=(1, 2))
                    elif key == 'Dist' and k == 0:
                        out[key][s, m, p, :, z] = pprod(mat3, axis=(0, 2))
                    elif key == 'TRT' and k == 0:
                        out[key][s, m, p, :, z] = pprod(mat4, axis=(1, 2, 3))
                    elif key == 'Mag_Dist' and k == 0:
                        out[key][s, m, p, ..., z] = pprod(mat3, axis=2)
                    elif key == 'Mag_Dist_Eps' and k == 0:
                        out[key][s, m, p, ..., z] = mat3
                    elif key == 'Mag_Dist_TRT' and k == 0:
                        out[key][s, m, p, ..., z] = pprod(  # T Ma D -> Ma D T
                            mat4, axis=(3)).transpose(1, 2, 0)
                    elif key == 'Mag_Dist_TRT_Eps' and k == 0:
                        out[key][s, m, p, ..., z] = mat4.transpose(1, 2, 0, 3)
                    elif key == 'Lon_Lat' and k == 1:
                        out[key][s, m, p, ..., z] = pprod(mat3, axis=0)
                    elif key == 'Mag_Lon_Lat' and k == 1:
                        out[key][s, m, p, ..., z] = mat3
                    elif key == 'Lon_Lat_TRT' and k == 1:
                        out[key][s, m, p, ..., z] = pprod(  # T Lo La -> Lo La T
                            mat4, axis=1).transpose(1, 2, 0)
                    # shape NMP..Z
        self.datastore['disagg'] = out
        # below a dataset useful for debugging, at minimum IMT and maximum RP
        self.datastore['_disagg_trt'] = _disagg_trt
        if len(vcurves):
            NML1 = len(vcurves), self.M, oq.imtls.size // self.M
            self.datastore['_vcurves'] = numpy.array(vcurves).reshape(NML1)
            self.datastore['_vcurves'].attrs['sids'] = numpy.where(count)[0]

        # check null realizations in the single site case, see disagg/case_2
        best_rlzs = self.datastore['best_rlzs'][:]  # (shape N, Z)
        for (s, z), r in numpy.ndenumerate(best_rlzs):
            lst = []
            for key in out:
                if out[key][s, ..., z].sum() == 0:
                    lst.append(key)
            if lst:
                logging.warning('No %s contributions for site=%d, rlz=%d',
                                lst, s, r)
