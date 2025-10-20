# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
import psutil
import numpy

from openquake.baselib import parallel
from openquake.baselib.general import (
    AccumDict, pprod, agg_probs, shortlist)
from openquake.baselib.python3compat import encode
from openquake.hazardlib import stats, map_array, valid
from openquake.hazardlib.calc import disagg, mean_rates
from openquake.hazardlib.contexts import read_cmakers, read_ctx_by_grp
from openquake.commonlib import util
from openquake.calculators import base, getters

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


def compute_disagg(dstore, ctxt, sitecol, cmaker, bin_edges, src_mutex, rwdic,
                   monitor):
    """
    :param dstore:
        a DataStore instance
    :param ctxt:
        a context array
    :param sitecol:
        a site collection
    :param cmaker:
        a ContextMaker instance
    :param bin_edges:
        a tuple of bin edges (mag, dist, lon, lat, eps, trt)
    :param src_mutex:
        a dictionary src_id -> weight, usually empty
    :param rwdic:
        dictionary rlz -> weight, empty for individual realizations
    :param monitor:
        monitor of the currently running job
    :returns:
        a list of dictionaries containing matrices of rates
    """
    mon0 = monitor('disagg mean_std', measuremem=False)
    mon1 = monitor('disagg by eps', measuremem=False)
    mon2 = monitor('composing pnes', measuremem=False)
    mon3 = monitor('disagg matrix', measuremem=False)
    out = []
    for site in sitecol:
        try:
            dis = disagg.Disaggregator([ctxt], site, cmaker, bin_edges)
        except disagg.FarAwayRupture:
            continue
        with dstore:
            iml2 = dstore['hmap3'][dis.sid]
            if iml2.sum() == 0:  # zero hard for this site
                continue

            imtls = {imt: iml2[m] for m, imt in enumerate(cmaker.imts)}
            rlzs = dstore['best_rlzs'][dis.sid]
        res = dis.disagg_by_magi(imtls, rlzs, rwdic, src_mutex,
                                 mon0, mon1, mon2, mon3)
        out.extend(res)
    return out


def get_outputs_size(shapedic, disagg_outputs, Z):
    """
    :returns: the total size of the outputs
    """
    tot = AccumDict(accum=0)
    for out in disagg_outputs:
        tot[out] = 8
        for key in out.lower().split('_'):
            tot[out] *= shapedic[key]
    return tot * shapedic['N'] * shapedic['M'] * shapedic['P'] * Z


def output_dict(shapedic, disagg_outputs, Z):
    N, M, P = shapedic['N'], shapedic['M'], shapedic['P']
    dic = {}
    for out in disagg_outputs:
        shp = tuple(shapedic[key] for key in out.lower().split('_'))
        dic[out] = numpy.zeros((N,) + shp + (M, P, Z))
    return dic


def submit(smap, dstore, ctxt, sitecol, cmaker, bin_edges, src_mutex, rwdic):
    mags = list(numpy.unique(ctxt.mag))
    logging.debug('Sending %d/%d sites for grp_id=%d, mags=%s',
                  len(sitecol), len(sitecol.complete), ctxt.grp_id[0],
                  shortlist(mags))
    smap.submit((dstore, ctxt, sitecol, cmaker, bin_edges, src_mutex, rwdic))


def check_memory(N, Z, shape8D):
    """
    Raise an error if the calculation will require too much memory
    """
    avail_gb = psutil.virtual_memory().available / 1024**3
    req_gb = numpy.prod(shape8D) * N * Z * 8 / 1024**3
    if avail_gb < req_gb*2:
        # req_gb*2 because when storing a lot more memory will be used
        raise MemoryError(
            'You have %.1f GB available but %.1f GB are required. '
            'The solution is to reduce the number of bins' %
            (avail_gb, req_gb*2))
    logging.info('The AccumDict will require %.1f GB', req_gb)


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
        all_edges, _shapedic = disagg.get_edges_shapedic(
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

    def execute(self):
        """Performs the disaggregation"""
        return self.full_disaggregation()

    def full_disaggregation(self):
        """
        Run the disaggregation phase.
        """
        oq = self.oqparam
        try:
            full_lt = self.full_lt
        except AttributeError:
            full_lt = self.datastore['full_lt'].init()
        if oq.rlz_index is None and oq.num_rlzs_disagg == 0:
            oq.num_rlzs_disagg = self.R  # 0 means all rlzs
        self.oqparam.mags_by_trt = self.datastore['source_mags']
        edges, self.shapedic = disagg.get_edges_shapedic(
            oq, self.sitecol, self.R)
        logging.info(self.shapedic)
        self.save_bin_edges(edges)
        self.poes_disagg = oq.poes_disagg or (None,)
        self.imts = list(oq.imtls)
        self.M = len(self.imts)
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        self.mgetters = getters.map_getters(dstore, full_lt, disagg=True)

        # build array rlzs (N, Z)
        if oq.rlz_index is None:
            Z = oq.num_rlzs_disagg
            rlzs = numpy.zeros((self.N, Z), int)
            if self.R > 1:
                for sid in range(self.N):
                    hcurve = self.mgetters[sid].get_hcurve(sid)
                    mean = getters.build_stat_curve(
                        hcurve, oq.imtls, stats.mean_curve, full_lt.weights,
                        full_lt.wget)
                    # get the closest realization to the mean
                    rlzs[sid] = util.closest_to_ref(hcurve.T, mean)[:Z]
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
        mean_curves = self.datastore.sel('hcurves-stats', stat='mean')[:, 0]
        s = self.shapedic
        if oq.iml_disagg:
            iml3 = numpy.zeros((s['N'], s['M'], 1))
            for m, imt in enumerate(oq.imtls):
                iml3[:, m] = oq.iml_disagg[imt]
        else:
            iml3 = map_array.compute_hmaps(
                mean_curves, oq.imtls, oq.poes)
        if iml3.sum() == 0:
            raise SystemExit('Cannot do any disaggregation: zero hazard')
        logging.info('Building N * M * P * Z = {:_d} intensities'.format(
                     s['N'] * s['M'] * s['P'] * s['Z']))
        self.datastore['hmap3'] = iml3
        self.datastore['poe4'] = numpy.zeros((s['N'], s['M'], s['P'], s['Z']))
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
        logging.info("Reading contexts")
        cmakers = read_cmakers(dstore).to_array()
        if 'src_mutex' in dstore:
            gb = dstore.read_df('src_mutex').groupby('grp_id')
            gp = dict(dstore['grp_probability'])  # grp_id -> probability
            src_mutex_by_grp = {
                grp_id: {'src_id': disagg.get_ints(df.src_id),
                         'weight': df.mutex_weight.to_numpy(),
                         'rup_mutex': df.rup_mutex.to_numpy(),
                         'grp_probability': gp[grp_id]}
                for grp_id, df in gb}
        else:
            src_mutex_by_grp = {}
        ctx_by_grp = read_ctx_by_grp(dstore)  # little memory used here
        totctxs = sum(len(ctx) for ctx in ctx_by_grp.values())
        logging.info('Read {:_d} contexts'.format(totctxs))
        self.datastore.swmr_on()
        smap = parallel.Starmap(compute_disagg, h5=self.datastore.hdf5)
        # IMPORTANT!! we rely on the fact that the classical part
        # of the calculation stores the ruptures in chunks of constant
        # grp_id, therefore it is possible to build (start, stop) slices;
        # we are NOT grouping by operator.itemgetter('grp_id', 'magi'):
        # that would break the ordering of the indices causing an incredibly
        # worse performance, but visible only in extra-large calculations!

        # compute the total weight of the contexts and the maxsize
        totweight = sum(cmakers[grp_id].Z * len(ctx)
                        for grp_id, ctx in ctx_by_grp.items())
        maxsize = int(numpy.ceil(totweight / (oq.concurrent_tasks or 1)))
        logging.debug(f'{totweight=}, {maxsize=}')

        s = self.shapedic
        if self.Z > 1:
            weights = self.datastore['weights'][:]
        else:
            weights = None
        for grp_id, ctxt in ctx_by_grp.items():
            cmaker = cmakers[grp_id]
            src_mutex = src_mutex_by_grp.get(grp_id, {})
            rup_mutex = src_mutex['rup_mutex'].any() if src_mutex else False

            # NB: in case_27 src_mutex for grp_id=1 has the form
            # {'src_id': array([1, 2]), 'weight': array([0.625, 0.375])}
            if rup_mutex:
                raise NotImplementedError(
                    'Disaggregation with mutex ruptures')

            # build rlz weight dictionary
            if weights is None:
                rwdic = {}  # don't compute means
            else:
                rwdic = {rlz: weights[rlz]
                         for rlzs in cmaker.gsims.values() for rlz in rlzs}

            # submit single task
            ntasks = len(ctxt) * cmaker.Z / maxsize
            if ntasks < 1 or len(src_mutex) or rup_mutex:
                # do not split (test case_11)
                submit(smap, self.datastore, ctxt, self.sitecol, cmaker,
                       self.bin_edges, src_mutex, rwdic)
                continue

            # split by tiles
            for tile_get in self.sitecol.split(ntasks):
                tile = tile_get(self.sitecol)
                ctx = ctxt[numpy.isin(ctxt.sids, tile.sids)]
                if len(ctx) * cmaker.Z > maxsize:
                    # split by magbin too
                    for c in disagg.split_by_magbin(
                            ctx, self.bin_edges[0]).values():
                        submit(smap, self.datastore, c, tile, cmaker,
                               self.bin_edges, src_mutex, rwdic)
                elif len(ctx):
                    # see case_multi in the oq-risk-tests
                    submit(smap, self.datastore, ctx, tile, cmaker,
                           self.bin_edges, src_mutex, rwdic)

        shape8D = (s['trt'], s['mag'], s['dist'], s['lon'], s['lat'], s['eps'],
                   s['M'], s['P'])
        check_memory(self.N, self.Z, shape8D)
        acc = AccumDict(accum=numpy.zeros(shape8D))
        # NB: a lot of memory can go in this AccumDict, please reduce the bins
        results = smap.reduce(self.agg_result, acc)
        return results  # s, r -> array 8D

    def agg_result(self, acc, results):
        """
        Collect the results coming from compute_disagg into self.results.

        :param acc: dictionary s, r -> array8D
        :param result: dictionary with the result coming from a task
        """
        with self.monitor('aggregating disagg matrices'):
            for res in results:
                trti = res.pop('trti')
                magi = res.pop('magi')
                sid = res.pop('sid')
                for rlz, arr in res.items():
                    acc[sid, rlz][trti, magi] += arr
        return acc

    def post_execute(self, results):
        """
        Save all the results of the disaggregation. NB: the number of results
        to save is #sites * #rlzs * #disagg_poes * #IMTs.

        :param results:
            a dictionary sid, rlz -> 8D disagg matrix
        """
        # the DEBUG dictionary is populated only for OQ_DISTRIBUTE=no
        for sid, pnes in disagg.DEBUG.items():
            print('site %d, mean pnes=%s' % (sid, pnes))
        mean = {}
        indv = {}
        for s, r in results:
            if r == 'mean':
                mean[s, 0] = results[s, r]
            else:
                indv[s, self.sr2z[s, r]] = results[s, r]
        with self.monitor('saving disagg results'):
            logging.info('Extracting and saving the PMFs')
            if indv:  # save individual realizations
                self.save_disagg_results(indv, 'disagg-rlzs')
            if mean:  # save mean PMFs
                self.save_disagg_results(mean, 'disagg-stats')

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

    def save_disagg_results(self, results, name):
        """
        Save the computed PMFs in the datastore.

        :param results:
            a dict s, z -> 8D-matrix of shape (T, Ma, D, E, Lo, La, M, P)
            containing individual realizations or statistics (only mean)
        :param name:
            the string "disagg-rlzs" or "disagg-stats"
        """
        oq = self.oqparam
        if name.endswith('rlzs'):
            Z = self.shapedic['Z']
        else:
            Z = 1  # only mean is supported
        out = output_dict(self.shapedic, oq.disagg_outputs, Z)
        _disagg_trt = numpy.zeros(self.N, [(trt, float) for trt in self.trts])
        best_rlzs = self.datastore['best_rlzs'][:]  # (shape N, Z)
        for (s, z), mat8 in sorted(results.items()):
            mat8 = disagg.to_probs(mat8)
            mat7 = agg_probs(*mat8)  # shape (Ma, D, E, Lo, La, M, P)
            for key in oq.disagg_outputs:
                if key == 'TRT':
                    out[key][s, ..., z] = valid.pmf_map[key](mat8)  # (T,M,P)
                elif key.startswith('TRT_'):
                    proj = valid.pmf_map[key[4:]]
                    out[key][s, ..., z] = [proj(m7) for m7 in mat8]
                else:
                    out[key][s, ..., z] = valid.pmf_map[key](mat7)

            # store poe4
            for m, imt in enumerate(self.imts):
                for p, poe in enumerate(self.poes_disagg):
                    mat6 = mat8[..., m, p]  # shape (T, Ma, D, Lo, La, E)
                    if m == 0 and poe == self.poes_disagg[-1]:
                        _disagg_trt[s] = tuple(
                            pprod(mat8[..., 0, 0], axis=(1, 2, 3, 4, 5)))
                    poe_agg = pprod(mat6, axis=(0, 1, 2, 3, 4, 5))
                    if name.endswith('-rlzs'):
                        self.datastore['poe4'][s, m, p, z] = max(
                            poe_agg, mean_rates.CUTOFF)

        self.datastore[name] = out
        for key in out:
            sd = ['site_id'] + key.split('_') + ['imt', 'poe', 'Z']
            self.datastore[f'{name}/{key}'].attrs['shape_descr'] = sd

        # below a dataset useful for debugging, at minimum IMT and maximum RP
        self.datastore['_disagg_trt'] = _disagg_trt

        # check null realizations in the single site case, see disagg/case_2
        if name.endswith('-rlzs'):
            for (s, z), r in numpy.ndenumerate(best_rlzs):
                lst = []
                for key in out:
                    if out[key][s, ..., z].sum() == 0:
                        lst.append(key)
                if lst:
                    logging.warning('No %s contributions for site=%d, rlz=%d',
                                    lst, s, r)
