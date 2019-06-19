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
from openquake.baselib.general import AccumDict, block_splitter
from openquake.baselib.python3compat import encode
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.contexts import RuptureContext, FEWSITES
from openquake.hazardlib.tom import PoissonTOM
from openquake.calculators import getters, extract
from openquake.calculators import base

weight = operator.attrgetter('weight')
DISAGG_RES_FMT = '%(rlz)s-%(imt)s-%(sid)s-%(poe)s/'
BIN_NAMES = 'mag', 'dist', 'lon', 'lat', 'eps', 'trt'


def _to_matrix(matrices, num_trts):
    # convert a dict trti -> matrix into a single matrix of shape (T, ...)
    trti = next(iter(matrices))
    mat = numpy.zeros((num_trts,) + matrices[trti].shape)
    for trti in matrices:
        mat[trti] = matrices[trti]
    return mat


def _iml2s(rlzs, iml_disagg, imtls, poes_disagg, curves):
    # a list of N arrays of shape (M, P) with intensities
    M = len(imtls)
    P = len(poes_disagg)
    imts = [from_string(imt) for imt in imtls]
    lst = []
    for s, curve in enumerate(curves):
        iml2 = numpy.empty((M, P))
        iml2.fill(numpy.nan)
        if poes_disagg == (None,):
            for m, imt in enumerate(imtls):
                iml2[m, 0] = imtls[imt]
        elif curve:
            for m, imt in enumerate(imtls):
                poes = curve[imt][::-1]
                imls = imtls[imt][::-1]
                iml2[m] = numpy.interp(poes_disagg, poes, imls)
        aw = hdf5.ArrayWrapper(
            iml2, dict(poes_disagg=poes_disagg, imts=imts, rlzi=rlzs[s]))
        lst.append(aw)
    return lst


def compute_disagg(sitecol, rupdata, cmaker, iml2s, trti, bin_edges,
                   oqparam, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param rupdata:
        rupdata array
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
    result = {'trti': trti, 'num_ruptures': 0}
    # all the time is spent in collect_bin_data
    RuptureContext.temporal_occurrence_model = PoissonTOM(
        oqparam.investigation_time)
    for sid, iml2 in zip(sitecol.sids, iml2s):
        singlesitecol = sitecol.filtered([sid])
        bin_data = disagg.collect_bin_data(
            rupdata, singlesitecol, cmaker, iml2,
            oqparam.truncation_level, oqparam.num_epsilon_bins, monitor)
        if bin_data:  # dictionary poe, imt, rlzi -> pne
            bins = disagg.get_bins(bin_edges, sid)
            for (poe, imt, rlzi), matrix in disagg.build_disagg_matrix(
                    bin_data, bins, monitor).items():
                result[sid, rlzi, poe, imt] = matrix
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
    precalc = 'classical'
    accept_precalc = ['classical', 'disaggregation']
    POE_TOO_BIG = '''\
You are trying to disaggregate for poe=%s.
However the source model produces at most probabilities
of %.7f for rlz=#%d, IMT=%s.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.'''

    def init(self):
        if self.N > FEWSITES:
            raise ValueError(
                'The max number of sites for disaggregation set in '
                'openquake.cfg is %d, but you have %s' % (FEWSITES, self.N))
        super().init()

    def execute(self):
        """Performs the disaggregation"""
        return self.full_disaggregation()

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
        for key, val in result.items():
            acc[key][trti] = agg_probs(acc[key].get(trti, 0), val)
        return acc

    def get_curve(self, sid, rlz_by_sid):
        """
        Get the hazard curve for the given site ID.
        """
        imtls = self.oqparam.imtls
        ws = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        pgetter = getters.PmapGetter(self.datastore, ws, numpy.array([sid]))
        rlz = rlz_by_sid[sid]
        try:
            pmap = pgetter.get(rlz)
        except ValueError:  # empty pmaps
            logging.info(
                'hazard curve contains all zero probabilities; '
                'skipping site %d, rlz=%d', sid, rlz.ordinal)
            return
        if sid not in pmap:
            return
        poes = pmap[sid].convert(imtls)
        for imt_str in imtls:
            if all(x == 0.0 for x in poes[imt_str]):
                logging.info(
                    'hazard curve contains all zero probabilities; '
                    'skipping site %d, rlz=%d, IMT=%s',
                    sid, rlz.ordinal, imt_str)
                return
        return poes

    def check_poes_disagg(self, curves, rlzs):
        """
        Raise an error if the given poes_disagg are too small compared to
        the hazard curves.
        """
        oq = self.oqparam
        for sid in self.sitecol.sids:
            poes = curves[sid]
            if poes is not None:
                for imt in oq.imtls:
                    max_poe = poes[imt].max()
                    for poe in oq.poes_disagg:
                        if poe > max_poe:
                            raise ValueError(self.POE_TOO_BIG % (
                                poe, max_poe, rlzs[sid], imt))

    def full_disaggregation(self):
        """
        Run the disaggregation phase.
        """
        oq = self.oqparam
        tl = oq.truncation_level
        src_filter = SourceFilter(self.sitecol, oq.maximum_distance)
        if hasattr(self, 'csm'):
            for sg in self.csm.src_groups:
                if sg.atomic:
                    raise NotImplemented('Atomic groups are not supported yet')
            if not self.csm.get_sources():
                raise RuntimeError('All sources were filtered away!')

        csm_info = self.datastore['csm_info']
        poes_disagg = oq.poes_disagg or (None,)
        R = len(self.rlzs_assoc.realizations)
        rlzs = extract.disagg_key(self.datastore).rlzs
        if oq.iml_disagg:
            self.poe_id = {None: 0}
            curves = [None] * len(self.sitecol)  # no hazard curves are needed
        else:
            self.poe_id = {poe: i for i, poe in enumerate(oq.poes_disagg)}
            curves = [self.get_curve(sid, rlzs) for sid in self.sitecol.sids]
            self.check_poes_disagg(curves, rlzs)
        iml2s = _iml2s(rlzs, oq.iml_disagg, oq.imtls, poes_disagg, curves)
        if oq.disagg_by_src:
            if R == 1:
                self.build_disagg_by_src(iml2s)
            else:
                logging.warning('disagg_by_src works only with 1 realization, '
                                'you have %d', R)

        eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

        # build trt_edges
        trts = tuple(csm_info.trts)
        trt_num = {trt: i for i, trt in enumerate(trts)}
        self.trts = trts

        # build mag_edges
        min_mag = csm_info.min_mag
        max_mag = csm_info.max_mag
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
        self.imldict = {}  # sid, rlzi, poe, imt -> iml
        for s in self.sitecol.sids:
            iml2 = iml2s[s]
            r = rlzs[s]
            logging.info('Site #%d, disaggregating for rlz=#%d', s, r)
            for p, poe in enumerate(oq.poes_disagg or [None]):
                for m, imt in enumerate(oq.imtls):
                    self.imldict[s, r, poe, imt] = iml2[m, p]

        for grp, dset in self.datastore['rup'].items():
            grp_id = int(grp[4:])
            trt = csm_info.trt_by_grp[grp_id]
            trti = trt_num[trt]
            rlzs_by_gsim = self.rlzs_assoc.get_rlzs_by_gsim(grp_id)
            cmaker = ContextMaker(
                trt, rlzs_by_gsim, src_filter.integration_distance,
                {'filter_distance': oq.filter_distance})
            for block in block_splitter(dset[()], 1000):
                all_args.append(
                    (src_filter.sitecol, numpy.array(block), cmaker, iml2s,
                     trti, self.bin_edges, oq))

        self.num_ruptures = [0] * len(self.trts)
        mon = self.monitor()
        results = parallel.Starmap(compute_disagg, all_args, mon).reduce(
            self.agg_result, AccumDict(accum={}))
        return results

    def save_bin_edges(self):
        """
        Save disagg-bins
        """
        b = self.bin_edges
        for sid in self.sitecol.sids:
            bins = disagg.get_bins(b, sid)
            shape = [len(bin) - 1 for bin in bins] + [len(self.trts)]
            shape_dic = dict(zip(BIN_NAMES, shape))
            logging.info('nbins=%s for site=#%d', shape_dic, sid)
            matrix_size = numpy.prod(shape)
            if matrix_size > 1E7:
                raise ValueError(
                    'The disaggregation matrix for site #%d is too large '
                    '(%d elements): fix the binnning!' % (sid, matrix_size))
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
            rlz='rlz-%d' % rlz_id, imt=imt_str, sid='sid-%d' % site_id,
            poe='poe-%d' % self.poe_id[poe])
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
        attrs['site_id'] = site_id
        attrs['rlzi'] = rlz_id
        attrs['imt'] = imt_str
        attrs['iml'] = self.imldict[site_id, rlz_id, poe, imt_str]
        attrs['mag_bin_edges'] = mag
        attrs['dist_bin_edges'] = dist
        attrs['lon_bin_edges'] = lons
        attrs['lat_bin_edges'] = lats
        attrs['eps_bin_edges'] = eps
        attrs['trt_bin_edges'] = self.trts
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
        ws = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        pgetter = getters.PmapGetter(self.datastore, ws, self.sitecol.sids)
        pmap_by_grp = pgetter.init()
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
