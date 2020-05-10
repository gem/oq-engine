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
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import (
    AccumDict, block_splitter, get_array_nbytes, humansize)
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
DISAGG_RES_FMT = '%(rlz)s%(imt)s-%(sid)s-%(poe)s/'
POE_TOO_BIG = '''\
Site #%d: you are trying to disaggregate for poe=%s.
However the source model produces at most probabilities
of %.7f for rlz=#%d, IMT=%s.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.'''


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


def _trt_matrix(matrices, num_trts):
    # convert a dict trti -> matrix into a single matrix of shape (T, ...)
    trti = next(iter(matrices))
    mat = numpy.zeros((num_trts,) + matrices[trti].shape)
    for trti in matrices:
        mat[trti] = matrices[trti]
    return mat


def _iml3(rlzs, iml_disagg, imtls, poes_disagg, curves):
    # a dictionary of ArrayWrappers imt -> (N, P, Z) with intensities
    N, Z = rlzs.shape
    P = len(poes_disagg)
    dic = {}
    for m, imt in enumerate(imtls):
        iml3 = numpy.empty((N, P, Z))
        iml3.fill(numpy.nan)
        for (s, z), rlz in numpy.ndenumerate(rlzs):
            curve = curves[s][z]
            if poes_disagg == (None,):
                iml3[s, 0, z] = imtls[imt]
            elif curve:
                poes = curve[imt][::-1]
                imls = imtls[imt][::-1]
                iml3[s, :, z] = numpy.interp(poes_disagg, poes, imls)
        dic[imt] = hdf5.ArrayWrapper(
            iml3, dict(imt=from_string(imt), imti=m, rlzs=rlzs))
    return dic


def compute_disagg(dstore, idxs, cmaker, iml3, trti, bin_edges, oq, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param dstore
        a DataStore instance
    :param idxs:
        an array of indices to ruptures
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param iml3:
        an ArrayWrapper of shape (N, P, Z) with an attribute imt
    :param trti:
        tectonic region type index
    :param bin_egdes:
        a quintet (mag_edges, dist_edges, lon_edges, lat_edges, eps_edges)
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary sid -> 8D-array
    """
    with monitor('reading rupdata', measuremem=True):
        dstore.open('r')
        sitecol = dstore['sitecol']
        rupdata = {k: dstore['rup/' + k][idxs] for k in dstore['rup']}
    RuptureContext.temporal_occurrence_model = PoissonTOM(
        oq.investigation_time)
    pne_mon = monitor('disaggregate_pne', measuremem=False)
    mat_mon = monitor('build_disagg_matrix', measuremem=True)
    gmf_mon = monitor('disagg mean_std', measuremem=False)
    for sid, iml2 in zip(sitecol.sids, iml3):
        singlesite = sitecol.filtered([sid])
        bins = disagg.get_bins(bin_edges, sid)
        gsim_by_z = {}
        for z in range(iml3.shape[-1]):
            try:
                gsim = cmaker.gsim_by_rlzi[iml3.rlzs[sid, z]]
            except KeyError:
                pass
            else:
                gsim_by_z[z] = gsim
        ctxs = []
        ok, = numpy.where(
            rupdata['rrup_'][:, sid] <= cmaker.maximum_distance(cmaker.trt))
        for ridx in ok:  # consider only the ruptures close to the site
            ctx = RuptureContext((par, rupdata[par][ridx])
                                 for par in rupdata if not par.endswith('_'))
            for par in rupdata:
                if par.endswith('_'):
                    setattr(ctx, par[:-1], rupdata[par][ridx, [sid]])
            ctxs.append(ctx)

        eps3 = disagg._eps3(cmaker.trunclevel, oq.num_epsilon_bins)
        matrix = numpy.zeros([len(b) - 1 for b in bins] + list(iml2.shape))
        for z, gsim in gsim_by_z.items():
            with gmf_mon:
                ms = disagg.get_mean_stdv(singlesite, ctxs, iml3.imt, gsim)
            bdata = disagg.disaggregate(
                ms, ctxs, iml3.imt, iml2[:, z], eps3, pne_mon)
            if bdata.pnes.sum():
                with mat_mon:
                    matrix[..., z] = disagg.build_disagg_matrix(bdata, bins)
        if matrix.any():
            yield {'trti': trti, 'imti': iml3.imti, sid: matrix}


def agg_probs(*probs):
    """
    Aggregate probabilities withe the usual formula 1 - (1 - P1) ... (1 - Pn)
    """
    acc = 1. - probs[0]
    for prob in probs[1:]:
        acc *= 1. - prob
    return 1. - acc


def get_indices(dstore, concurrent_tasks):
    acc = AccumDict(accum=[])  # grp_id -> indices
    n = 0
    grp_ids = dstore['grp_ids'][()]
    for idx, gidx in enumerate(dstore['rup/grp_id'][()]):
        n += len(grp_ids[gidx])
        for grp_id in grp_ids[gidx]:
            acc[grp_id].append(idx)
    blocksize = numpy.ceil(n / concurrent_tasks)
    indices = []
    for grp_id in dstore['full_lt'].trt_by_grp:
        blocks = list(block_splitter(acc[grp_id], blocksize))
        indices.append(blocks)
    return indices


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
        all_edges, shapedic = disagg.get_edges_shapedic(
            oq, self.sitecol, mags_by_trt)
        *self.bin_edges, self.trts = all_edges
        src_filter = self.src_filter()
        if hasattr(self, 'csm'):
            for sg in self.csm.src_groups:
                if sg.atomic:
                    raise NotImplementedError(
                        'Atomic groups are not supported yet')

        self.full_lt = self.datastore['full_lt']
        self.poes_disagg = oq.poes_disagg or (None,)
        self.imts = list(oq.imtls)

        self.ws = [rlz.weight for rlz in self.full_lt.get_realizations()]
        self.pgetter = getters.PmapGetter(
            self.datastore, self.ws, self.sitecol.sids)

        # build array rlzs (N, Z)
        if oq.rlz_index is None:
            Z = oq.num_rlzs_disagg
            rlzs = numpy.zeros((self.N, Z), int)
            if self.R > 1:
                for sid in self.sitecol.sids:
                    curves = numpy.array(
                        [pc.array for pc in self.pgetter.get_pcurves(sid)])
                    mean = getters.build_stat_curve(
                        curves, oq.imtls, stats.mean_curve, self.ws)
                    rlzs[sid] = util.closest_to_ref(curves, mean.array)[:Z]
                self.datastore['best_rlzs'] = rlzs
        else:
            Z = len(oq.rlz_index)
            rlzs = numpy.zeros((self.N, Z), int)
            for z in range(Z):
                rlzs[:, z] = oq.rlz_index[z]
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
        self.iml3 = _iml3(rlzs, oq.iml_disagg, oq.imtls,
                          self.poes_disagg, curves)
        if oq.disagg_by_src:
            self.build_disagg_by_src(rlzs)

        self.save_bin_edges()
        sd = shapedic.copy()
        sd.pop('trt')
        nbytes, msg = get_array_nbytes(sd)
        if nbytes > oq.max_data_transfer:
            raise ValueError(
                'Estimated data transfer too big\n%s > max_data_transfer=%s' %
                (msg, humansize(oq.max_data_transfer)))
        logging.info('Estimated data transfer:\n%s', msg)
        tot = get_outputs_size(shapedic, oq.disagg_outputs or disagg.pmf_map)
        logging.info('Total output size: %s', humansize(sum(tot.values())))
        self.imldic = {}  # sid, rlz, poe, imt -> iml
        for s in self.sitecol.sids:
            for z, rlz in enumerate(rlzs[s]):
                for p, poe in enumerate(self.poes_disagg):
                    for imt in oq.imtls:
                        self.imldic[s, rlz, poe, imt] = self.iml3[imt][s, p, z]

        # submit #groups disaggregation tasks
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        M = len(oq.imtls)
        tasks_per_imt = numpy.ceil(oq.concurrent_tasks / M) or 1
        rups_per_task = len(dstore['rup/mag']) / tasks_per_imt
        logging.info('Considering ~%d ruptures per task', rups_per_task)
        indices = get_indices(dstore, tasks_per_imt)
        self.datastore.swmr_on()
        smap = parallel.Starmap(compute_disagg, h5=self.datastore.hdf5)
        trt_num = {trt: i for i, trt in enumerate(self.trts)}
        for grp_id, trt in self.full_lt.trt_by_grp.items():
            logging.info('Group #%d, sending rup_data for %s', grp_id, trt)
            trti = trt_num[trt]
            cmaker = ContextMaker(
                trt, self.full_lt.get_rlzs_by_gsim(grp_id),
                {'truncation_level': oq.truncation_level,
                 'maximum_distance': src_filter.integration_distance,
                 'filter_distance': oq.filter_distance, 'imtls': oq.imtls})
            for idxs in indices[grp_id]:
                for imt in oq.imtls:
                    smap.submit((dstore, idxs, cmaker, self.iml3[imt], trti,
                                 self.bin_edges, oq))
        results = smap.reduce(self.agg_result, AccumDict(accum={}))
        return results  # sid -> trti-> 8D array

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results.

        :param acc: dictionary imti, sid -> trti -> 7D array
        :param result: dictionary with the result coming from a task
        """
        # 7D array of shape (#magbins, #distbins, #lonbins, #latbins, #epsbins,
        #                    P, Z)
        with self.monitor('aggregating disagg matrices'):
            trti = result.pop('trti')
            imti = result.pop('imti')
            for sid, probs in result.items():
                before = acc[imti, sid].get(trti, 0)
                acc[imti, sid][trti] = agg_probs(before, probs)
        return acc

    def save_bin_edges(self):
        """
        Save disagg-bins
        """
        b = self.bin_edges
        T = len(self.trts)
        shape = [len(bin) - 1 for bin in disagg.get_bins(b, 0)] + [T]
        matrix_size = numpy.prod(shape)  # 6D
        if matrix_size > 1E6:
            raise ValueError(
                'The disaggregation matrix is too large '
                '(%d elements): fix the binning!' % matrix_size)
        self.datastore['disagg-bins/mags'] = b[0]
        self.datastore['disagg-bins/dists'] = b[1]
        for sid in self.sitecol.sids:
            self.datastore['disagg-bins/lons/sid-%d' % sid] = b[2][sid]
            self.datastore['disagg-bins/lats/sid-%d' % sid] = b[3][sid]
        self.datastore['disagg-bins/eps'] = b[4]

    def post_execute(self, results):
        """
        Save all the results of the disaggregation. NB: the number of results
        to save is #sites * #rlzs * #disagg_poes * #IMTs.

        :param results:
            a dictionary sid -> trti -> disagg matrix
        """
        T = len(self.trts)
        # build a dictionary m, s -> 8D matrix of shape (T, ..., E, P)
        results = {ms: _trt_matrix(dic, T) for ms, dic in results.items()}

        # get the number of outputs
        shp = (self.N, len(self.poes_disagg), len(self.imts), self.Z)
        logging.info('Extracting and saving the PMFs for %d outputs '
                     '(N=%s, P=%d, M=%d, Z=%d)', numpy.prod(shp), *shp)
        self.save_disagg_results(results, trts=encode(self.trts))

    def save_disagg_results(self, results, **attrs):
        """
        Save the computed PMFs in the datastore

        :param results:
            a dict (m, s) -> 8D-matrix of shape (T, .., E, P)
        :param attrs:
            dictionary of attributes to add to the dataset
        """
        imts = list(self.oqparam.imtls)
        for (m, s), mat8 in results.items():
            imt = imts[m]
            rlzs = self.rlzs[s]
            many_rlzs = len(rlzs) > 1
            if many_rlzs:  # rescale the weights
                weights = numpy.array([self.ws[r][imt] for r in rlzs])
                weights /= weights.sum()  # normalize to 1
            for p, poe in enumerate(self.poes_disagg):
                mat7 = mat8[..., p, :]
                for z in range(self.Z):
                    mat6 = mat7[..., z]
                    if mat6.any():  # nonzero
                        self._save('disagg', s, rlzs[z], poe, imt, mat6)
                if many_rlzs:  # compute the mean matrices
                    mean = numpy.average(mat7, -1, weights)
                    if mean.any():  # nonzero
                        self._save('disagg', s, 'mean', poe, imt, mean)
        self.datastore.set_attrs('disagg', **attrs)

    def _save(self, dskey, site_id, rlz_id, poe, imt_str, matrix6):
        disagg_outputs = self.oqparam.disagg_outputs
        lon = self.sitecol.lons[site_id]
        lat = self.sitecol.lats[site_id]
        try:
            rlz = 'rlz-%d-' % rlz_id
        except TypeError:  # for the mean
            rlz = ''
        disp_name = dskey + '/' + DISAGG_RES_FMT % dict(
            rlz=rlz, imt=imt_str, sid='sid-%d' % site_id,
            poe='poe-%d' % self.poe_id[poe])
        mag, dist, lonsd, latsd, eps = self.bin_edges
        lons, lats = lonsd[site_id], latsd[site_id]
        with self.monitor('extracting PMFs'):
            poe_agg = []
            aggmatrix = agg_probs(*matrix6)
            for key, fn in disagg.pmf_map.items():
                if not disagg_outputs or key in disagg_outputs:
                    pmf = fn(matrix6 if key.endswith('TRT') else aggmatrix)
                    self.datastore[disp_name + key] = pmf
                    poe_agg.append(1. - numpy.prod(1. - pmf))

        attrs = self.datastore.hdf5[disp_name].attrs
        attrs['site_id'] = site_id
        attrs['rlzi'] = rlz_id
        attrs['imt'] = imt_str
        try:
            attrs['iml'] = self.imldic[site_id, rlz_id, poe, imt_str]
        except KeyError:  # for the mean
            pass
        attrs['mag_bin_edges'] = mag
        attrs['dist_bin_edges'] = dist
        attrs['lon_bin_edges'] = lons
        attrs['lat_bin_edges'] = lats
        attrs['eps_bin_edges'] = eps
        attrs['trt_bin_edges'] = self.trts
        attrs['location'] = (lon, lat)
        # sanity check: all poe_agg should be the same
        attrs['poe_agg'] = poe_agg
        if poe and site_id in self.ok_sites:
            attrs['poe'] = poe
            poe_agg = numpy.mean(attrs['poe_agg'])
            if abs(1 - poe_agg / poe) > .1:
                logging.warning(
                    'Site #%d: poe_agg=%s is quite different from the expected'
                    ' poe=%s; perhaps the number of intensity measure'
                    ' levels is too small?', site_id, poe_agg, poe)

    def build_disagg_by_src(self, rlzs):
        logging.warning('Disaggregation by source is experimental')
        oq = self.oqparam
        groups = list(self.full_lt.get_rlzs_by_grp())
        M = len(oq.imtls)
        P = len(self.poes_disagg)
        for (s, z), rlz in numpy.ndenumerate(rlzs):
            poes = numpy.zeros((M, P, len(groups)))
            rlz = rlzs[s, z]
            for g, grp_id in enumerate(groups):
                pcurve = self.pgetter.get_pcurve(s, rlz, int(grp_id[4:]))
                if pcurve is None:
                    continue
                for m, imt in enumerate(oq.imtls):
                    xs = oq.imtls[imt]
                    ys = pcurve.array[oq.imtls(imt), 0]
                    poes[m, :, g] = numpy.interp(
                        self.iml3[imt][s, :, z], xs, ys)
            for m, imt in enumerate(oq.imtls):
                for p, poe in enumerate(self.poes_disagg):
                    pref = ('iml-%s' % oq.iml_disagg[imt] if poe is None
                            else 'poe-%s' % poe)
                    name = 'disagg_by_src/%s-%s-sid-%s' % (pref, imt, s)
                    if poes[m, p].sum():  # nonzero contribution
                        poe_agg = 1 - numpy.prod(1 - poes[m, p])
                        if poe and abs(1 - poe_agg / poe) > .1:
                            logging.warning(
                                'poe_agg=%s is quite different from '
                                'the expected poe=%s', poe_agg, poe)
                        self.datastore[name] = poes[m, p]
                        self.datastore.set_attrs(name, poe_agg=poe_agg)
