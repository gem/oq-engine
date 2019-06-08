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

"""
Disaggregation calculator core functionality
"""
import logging
import operator
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import AccumDict, groupby, block_splitter
from openquake.baselib.python3compat import encode
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.calculators import getters
from openquake.calculators import base, classical

weight = operator.attrgetter('weight')
DISAGG_RES_FMT = '%(poe)s%(rlz)s-%(imt)s-sid-%(sid)s/'


def _to_matrix(matrices, num_trts):
    # convert a dict trti -> matrix into a single matrix of shape (T, ...)
    trti = next(iter(matrices))
    mat = numpy.zeros((num_trts,) + matrices[trti].shape)
    for trti in matrices:
        mat[trti] = matrices[trti]
    return mat


def _iml2s(rlzis, iml_disagg, imtls, poes_disagg, curves):
    # a list of N arrays of shape (M, P) with intensities
    M = len(imtls)
    P = len(poes_disagg)
    imts = [from_string(imt) for imt in imtls]
    lst = []
    for s, curve in enumerate(curves):
        iml2 = numpy.empty((M, P))
        iml2.fill(numpy.nan)
        if poes_disagg == (None,):
            r = 0
            for m, imt in enumerate(imtls):
                iml2[m, 0] = imtls[imt]
        elif curve:
            r = rlzis[s]
            for m, imt in enumerate(imtls):
                poes = curve[r][imt][::-1]
                imls = imtls[imt][::-1]
                iml2[m] = numpy.interp(poes_disagg, poes, imls)
        aw = hdf5.ArrayWrapper(
            iml2, dict(poes_disagg=poes_disagg, imts=imts, rlzi=r))
        lst.append(aw)
    return lst


def compute_disagg(sitecol, sources, cmaker, iml2s, trti, bin_edges,
                   oqparam, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param sources:
        list of hazardlib source objects
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param iml2s:
        a list of N arrays of shape (M, P)
    :param dict trti:
        tectonic region type index
    :param bin_egdes:
        a quintet (mag_edges, dist_edges, lon_edges, lat_edges, eps_edges)
    :param oqparam:
        the parameters in the job.ini file
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary of probability arrays, with composite key
        (sid, rlzi, poe, imt, iml, trti).
    """
    result = {'trti': trti, 'num_ruptures': 0,
              'cache_info': numpy.zeros(3)}
    # all the time is spent in collect_bin_data
    ruptures = []
    for src in sources:
        ruptures.extend(src.iter_ruptures())
    for sid, iml2 in zip(sitecol.sids, iml2s):
        singlesitecol = sitecol.filtered([sid])
        bin_data = disagg.collect_bin_data(
            ruptures, singlesitecol, cmaker, iml2,
            oqparam.truncation_level, oqparam.num_epsilon_bins, monitor)
        if bin_data:  # dictionary poe, imt, rlzi -> pne
            bins = disagg.get_bins(bin_edges, sid)
            for (poe, imt, rlzi), matrix in disagg.build_disagg_matrix(
                    bin_data, bins, monitor).items():
                result[sid, rlzi, poe, imt] = matrix
        result['cache_info'] += monitor.cache_info
        result['num_ruptures'] += len(bin_data.mags)
    return result  # sid, rlzi, poe, imt, iml -> array


def agg_probs(*probs):
    """
    Aggregate probabilities withe the usual formula 1 - (1 - P1) ... (1 - Pn)
    """
    acc = 1. - probs[0]
    for prob in probs[1:]:
        acc *= 1. - prob
    return 1. - acc


@base.calculators.add('disaggregation')
class DisaggregationCalculator(base.HazardCalculator):
    """
    Classical PSHA disaggregation calculator
    """
    accept_precalc = ['psha']
    POE_TOO_BIG = '''\
You are trying to disaggregate for poe=%s.
However the source model #%d, '%s',
produces at most probabilities of %.7f for rlz=#%d, IMT=%s.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.'''

    def pre_execute(self):
        oq = self.oqparam
        if oq.iml_disagg and not oq.disagg_by_src:
            base.HazardCalculator.pre_execute(self)
        else:
            # we need to run a ClassicalCalculator
            cl = classical.ClassicalCalculator(oq, self.datastore.calc_id)
            cl.run()
            self.csm = cl.csm
            self.rlzs_assoc = cl.rlzs_assoc  # often reduced logic tree
            self.sitecol = cl.sitecol

    def execute(self):
        """Performs the disaggregation"""
        oq = self.oqparam
        if oq.iml_disagg:
            curves = [None] * len(self.sitecol)  # no hazard curves are needed
        else:
            curves = [self.get_curves(sid) for sid in self.sitecol.sids]
            self.check_poes_disagg(curves)
        return self.full_disaggregation(curves)

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results,
        a dictionary with key (sid, rlzi, poe, imt, trti)
        and values which are probability arrays.

        :param acc: dictionary k -> dic accumulating the results
        :param result: dictionary with the result coming from a task
        """
        # this is fast
        trti = result.pop('trti')
        self.num_ruptures[trti] += result.pop('num_ruptures')
        self.cache_info += result.pop('cache_info', 0)
        for key, val in result.items():
            acc[key][trti] = agg_probs(acc[key].get(trti, 0), val)
        return acc

    def get_curves(self, sid):
        """
        Get all the relevant hazard curves for the given site ordinal.
        Returns a dictionary rlz_id -> curve_by_imt.
        """
        dic = {}
        imtls = self.oqparam.imtls
        by_grp = self.rlzs_assoc.by_grp()
        ws = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        pgetter = getters.PmapGetter(
            self.datastore, by_grp, ws, numpy.array([sid]))
        for rlz in self.rlzs_assoc.realizations:
            try:
                pmap = pgetter.get(rlz.ordinal)
            except ValueError:  # empty pmaps
                logging.info(
                    'hazard curve contains all zero probabilities; '
                    'skipping site %d, rlz=%d', sid, rlz.ordinal)
                continue
            if sid not in pmap:
                continue
            poes = pmap[sid].convert(imtls)
            for imt_str in imtls:
                if all(x == 0.0 for x in poes[imt_str]):
                    logging.info(
                        'hazard curve contains all zero probabilities; '
                        'skipping site %d, rlz=%d, IMT=%s',
                        sid, rlz.ordinal, imt_str)
                    continue
                dic[rlz.ordinal] = poes
        return dic

    def check_poes_disagg(self, curves):
        """
        Raise an error if the given poes_disagg are too small compared to
        the hazard curves.
        """
        oq = self.oqparam
        max_poe = numpy.zeros(len(self.rlzs_assoc.realizations), oq.imt_dt())

        # check for too big poes_disagg
        for smodel in self.csm.source_models:
            sm_id = smodel.ordinal
            for sid, site in enumerate(self.sitecol):
                for rlzi, poes in curves[sid].items():
                    for imt in oq.imtls:
                        max_poe[rlzi][imt] = max(
                            max_poe[rlzi][imt], poes[imt].max())
            for poe in oq.poes_disagg:
                for rlz in self.rlzs_assoc.rlzs_by_smodel[sm_id]:
                    rlzi = rlz.ordinal
                    for imt in oq.imtls:
                        min_poe = max_poe[rlzi][imt]
                        if poe > min_poe:
                            raise ValueError(self.POE_TOO_BIG % (
                                poe, sm_id, smodel.names, min_poe, rlzi, imt))

    def full_disaggregation(self, curves):
        """
        Run the disaggregation phase.

        :param curves: a list of hazard curves, one per site

        The curves can be all None if iml_disagg is set in the job.ini
        """
        oq = self.oqparam
        tl = oq.truncation_level
        src_filter = SourceFilter(self.sitecol, oq.maximum_distance)
        csm = self.csm
        for sg in csm.src_groups:
            if sg.atomic:
                raise NotImplemented('Atomic groups are not supported yet')
        if not csm.get_sources():
            raise RuntimeError('All sources were filtered away!')

        poes_disagg = oq.poes_disagg or (None,)
        N = len(self.sitecol)
        R = len(self.rlzs_assoc.realizations)
        if oq.rlz_index is None:
            try:
                rlzs = self.datastore['best_rlz'][()]
            except KeyError:
                rlzs = numpy.zeros(N, int)
        else:
            rlzs = [oq.rlz_index] * N
        iml2s = _iml2s(rlzs, oq.iml_disagg, oq.imtls, poes_disagg, curves)
        if oq.disagg_by_src:
            if R == 1:
                self.build_disagg_by_src(iml2s)
            else:
                logging.warning('disagg_by_src works only with 1 realization, '
                                'you have %d', R)

        eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

        # build trt_edges
        trts = tuple(sorted(set(sg.trt for smodel in csm.source_models
                                for sg in smodel.src_groups)))
        trt_num = {trt: i for i, trt in enumerate(trts)}
        self.trts = trts

        # build mag_edges
        mmm = numpy.array([src.get_min_max_mag() for src in csm.get_sources()])
        min_mag = mmm[:, 0].min()
        max_mag = mmm[:, 1].max()
        mag_edges = oq.mag_bin_width * numpy.arange(
            int(numpy.floor(min_mag / oq.mag_bin_width)),
            int(numpy.ceil(max_mag / oq.mag_bin_width) + 1))

        # build dist_edges
        maxdist = max(oq.maximum_distance(trt, max_mag) for trt in trts)
        dist_edges = oq.distance_bin_width * numpy.arange(
            0, int(numpy.ceil(maxdist / oq.distance_bin_width) + 1))

        # build eps_edges
        eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

        # build lon_edges, lat_edges per sid
        bbs = src_filter.get_bounding_boxes(mag=max_mag)
        lon_edges, lat_edges = {}, {}  # by sid
        for sid, bb in zip(self.sitecol.sids, bbs):
            lon_edges[sid], lat_edges[sid] = disagg.lon_lat_bins(
                bb, oq.coordinate_bin_width)
        self.bin_edges = mag_edges, dist_edges, lon_edges, lat_edges, eps_edges
        self.save_bin_edges()

        # build all_args
        all_args = []
        maxweight = csm.get_maxweight(weight, oq.concurrent_tasks)
        self.imldict = {}  # sid, rlzi, poe, imt -> iml
        for s in self.sitecol.sids:
            iml2 = iml2s[s]
            r = rlzs[s]
            for p, poe in enumerate(oq.poes_disagg or [None]):
                for m, imt in enumerate(oq.imtls):
                    self.imldict[s, r, poe, imt] = iml2[m, p]

        for smodel in csm.source_models:
            sm_id = smodel.ordinal
            for trt, groups in groupby(
                    smodel.src_groups, operator.attrgetter('trt')).items():
                trti = trt_num[trt]
                sources = sum([grp.sources for grp in groups], [])
                rlzs_by_gsim = self.rlzs_assoc.get_rlzs_by_gsim(trt, sm_id)
                cmaker = ContextMaker(
                    trt, rlzs_by_gsim, src_filter.integration_distance,
                    {'filter_distance': oq.filter_distance})
                for block in block_splitter(sources, maxweight, weight):
                    all_args.append(
                        (src_filter.sitecol, block, cmaker, iml2s, trti,
                         self.bin_edges, oq))

        self.num_ruptures = [0] * len(self.trts)
        self.cache_info = numpy.zeros(3)  # operations, cache_hits, num_zeros
        mon = self.monitor()
        mon.cache_info = numpy.zeros(3)
        results = parallel.Starmap(compute_disagg, all_args, mon).reduce(
            self.agg_result, AccumDict(accum={}))

        # set eff_ruptures
        trti = csm.info.trt2i()
        for smodel in csm.info.source_models:
            for sg in smodel.src_groups:
                sg.eff_ruptures = self.num_ruptures[trti[sg.trt]]
        self.datastore['csm_info'] = csm.info

        ops, hits, num_zeros = self.cache_info
        logging.info('Cache speedup %s', ops / (ops - hits))
        logging.info('Discarded zero matrices: %d', num_zeros)
        return results

    def save_bin_edges(self):
        """
        Save disagg-bins
        """
        b = self.bin_edges
        for sid in self.sitecol.sids:
            bins = disagg.get_bins(b, sid)
            shape = [len(bin) - 1 for bin in bins] + [len(self.trts)]
            logging.info('disagg_matrix_shape=%s, site=#%d', str(shape), sid)
            matrix_size = numpy.prod(shape)
            if matrix_size > 1E6:
                raise ValueError(
                    'The disaggregation matrix for site #%d is too large '
                    '(%d elements): fix the binnning!', matrix_size)
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
            a dictionary (sid, rlzi, poe, imt) -> trti -> disagg matrix
        """
        T = len(self.trts)
        # build a dictionary (sid, rlzi, poe, imt) -> 6D matrix
        results = {k: _to_matrix(v, T) for k, v in results.items()}

        # get the number of outputs
        shp = (len(self.sitecol), len(self.oqparam.poes_disagg or (None,)),
               len(self.oqparam.imtls))  # N, P, M
        logging.info('Extracting and saving the PMFs for %d outputs '
                     '(N=%s, P=%d, M=%d)', numpy.prod(shp), *shp)
        self.save_disagg_result(results, trts=encode(self.trts),
                                num_ruptures=self.num_ruptures)

    def save_disagg_result(self, results, **attrs):
        """
        Save the computed PMFs in the datastore

        :param results:
            a dictionary sid, rlz, poe, imt -> 6D disagg_matrix
        """
        for (sid, rlz, poe, imt), matrix in sorted(results.items()):
            self._save_result('disagg', sid, rlz, poe, imt, matrix)
        self.datastore.set_attrs('disagg', **attrs)

    def _save_result(self, dskey, site_id, rlz_id, poe, imt_str, matrix):
        disagg_outputs = self.oqparam.disagg_outputs
        lon = self.sitecol.lons[site_id]
        lat = self.sitecol.lats[site_id]
        disp_name = dskey + '/' + DISAGG_RES_FMT % dict(
            poe='' if poe is None else 'poe-%s-' % poe,
            rlz='rlz-%d' % rlz_id, imt=imt_str, sid=site_id)
        mag, dist, lonsd, latsd, eps = self.bin_edges
        lons, lats = lonsd[site_id], latsd[site_id]
        with self.monitor('extracting PMFs'):
            poe_agg = []
            aggmatrix = agg_probs(*matrix)
            for key, fn in disagg.pmf_map.items():
                if not disagg_outputs or key in disagg_outputs:
                    pmf = fn(matrix if key.endswith('TRT') else aggmatrix)
                    self.datastore[disp_name + key] = pmf
                    poe_agg.append(1. - numpy.prod(1. - pmf))

        attrs = self.datastore.hdf5[disp_name].attrs
        attrs['rlzi'] = rlz_id
        attrs['imt'] = imt_str
        attrs['iml'] = self.imldict[site_id, rlz_id, poe, imt_str]
        attrs['mag_bin_edges'] = mag
        attrs['dist_bin_edges'] = dist
        attrs['lon_bin_edges'] = lons
        attrs['lat_bin_edges'] = lats
        attrs['eps_bin_edges'] = eps
        attrs['location'] = (lon, lat)
        # sanity check: all poe_agg should be the same
        attrs['poe_agg'] = poe_agg
        if poe:
            attrs['poe'] = poe
            poe_agg = numpy.mean(attrs['poe_agg'])
            if abs(1 - poe_agg / poe) > .1:
                logging.warning(
                    'poe_agg=%s is quite different from the expected'
                    ' poe=%s; perhaps the number of intensity measure'
                    ' levels is too small?', poe_agg, poe)

    def build_disagg_by_src(self, iml2s):
        """
        :param dstore: a datastore
        :param iml2s: N arrays of IMLs with shape (M, P)
        """
        logging.warning('Disaggregation by source is experimental')
        oq = self.oqparam
        poes_disagg = oq.poes_disagg or (None,)
        by_grp = self.rlzs_assoc.by_grp()
        ws = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        pmap_by_grp = getters.PmapGetter(
            self.datastore, by_grp, ws, self.sitecol.sids).pmap_by_grp
        grp_ids = numpy.array(sorted(int(grp[4:]) for grp in pmap_by_grp))
        G = len(pmap_by_grp)
        P = len(poes_disagg)
        for rec in self.sitecol.array:
            sid = rec['sids']
            iml2 = iml2s[sid]
            for imti, imt in enumerate(oq.imtls):
                xs = oq.imtls[imt]
                poes = numpy.zeros((G, P))
                for g, grp_id in enumerate(grp_ids):
                    pmap = pmap_by_grp['grp-%02d' % grp_id]
                    if sid in pmap:
                        ys = pmap[sid].array[oq.imtls(imt), 0]
                        poes[g] = numpy.interp(iml2[imti, :], xs, ys)
                for p, poe in enumerate(poes_disagg):
                    prefix = ('iml-%s' % oq.iml_disagg[imt] if poe is None
                              else 'poe-%s' % poe)
                    name = 'disagg_by_src/%s-%s-%s-%s' % (
                        prefix, imt, rec['lon'], rec['lat'])
                    if poes[:, p].sum():  # nonzero contribution
                        poe_agg = 1 - numpy.prod(1 - poes[:, p])
                        if poe and abs(1 - poe_agg / poe) > .1:
                            logging.warning(
                                'poe_agg=%s is quite different from '
                                'the expected poe=%s', poe_agg, poe)
                        self.datastore[name] = poes[:, p]
                        self.datastore.set_attrs(name, poe_agg=poe_agg)
